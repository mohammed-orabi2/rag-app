from app.core.agents.agents import *
from langchain_core.messages import HumanMessage
from .models import *
from langgraph.graph import StateGraph, START, END
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree
from typing import Optional, List
from utils.formatting_utils import convert_db_messages_to_langchain
import json
import re


class WorkFlow:

    def __init__(self):
        self.rewrite_query_agent = rewrite_query_agent
        self.general_question_agent = general_question_agent
        self.sg_bot_agent = sg_bot_agent
        self.rules_agent = rules_agent
        self.follow_up_agent = follow_up_agent
        self.query_classification_agent = query_classification_agent
        self.filter_parameters_extraction_agent = filter_parameters_extraction_agent
        self.child_parent_retriever_agent = child_parent_retriever_agent
        # self.relevant_docs_id = relevant_docs_agent
        self.graph = self._build_graph()
        self.current_run_id = None

    def _build_graph(self):
        graph = StateGraph(State)

        # Add nodes
        # graph.add_node("rewrite_query", self.rewrite_query_agent)
        # graph.add_node("query_classification", self.query_classification_agent)
        graph.add_node("rewrite_query_agent", self.rewrite_query_agent)
        graph.add_node("query_classification_agent", self.query_classification_agent)
        graph.add_node("general_question", self.general_question_agent)
        graph.add_node("rules", self.rules_agent)
        graph.add_node("follow_up", self.follow_up_agent)
        graph.add_node("child_parent_retriever", self.child_parent_retriever_agent)
        graph.add_node(
            "filter_parameters_extraction", self.filter_parameters_extraction_agent
        )
        graph.add_node("sg_bot", self.sg_bot_agent)
        # graph.add_node("relevant_docs_id", self.relevant_docs_id)

        # Connect nodes
        graph.add_edge(START, "rewrite_query_agent")
        graph.add_edge("rewrite_query_agent", "query_classification_agent")
        # Five-way conditional routing
        graph.add_conditional_edges(
            "query_classification_agent",  # Analyzes and categorizes the user's question
            lambda state: state.get(
                "question_category", "general"
            ),  # Extracts the question_category from the current state. If no category is found, it defaults to "general"
            {
                "program_selection": "filter_parameters_extraction",  # Destination mapping
                "rules": "rules",
                "follow_up": "follow_up",
                "general": "general_question",
            },
        )

        graph.add_edge("rules", END)
        graph.add_edge("follow_up", END)
        graph.add_edge("general_question", END)
        graph.add_edge("filter_parameters_extraction", "child_parent_retriever")

        graph.add_edge("child_parent_retriever", "sg_bot")
        graph.add_edge("sg_bot", END)
        # graph.add_edge("relevant_docs_id", END)

        return graph.compile()

    @traceable(name="Counseling-Bot")
    async def stream_workflow(
        self,
        user_message,
        excluded_ids: list = None,
        conversation_messages: Optional[List] = None,
        username: str = None,
    ):
        """
        Stream user message processing through the compiled graph.
        Only yields string content chunks - metadata is stored in instance attributes.
        Returns the run_id when streaming is complete.
        """
        try:

            # Define nodes that can stream
            STREAMING_NODES = [
                "general_question",
                "rules",
                "follow_up",
                "sg_bot",
            ]

            # Try to get current run_id from tracing context
            current_run = get_current_run_tree()
            self.current_run_id = str(current_run.id) if current_run else None

            # Add username to LangSmith trace metadata if available
            if current_run and username:
                try:
                    from langsmith import update_current_run

                    update_current_run(metadata={"username": username})
                except Exception as e:
                    print(f"Warning: Failed to update LangSmith metadata: {e}")

            # Handle conversation messages safely
            if conversation_messages:
                # Convert database format to LangChain messages
                converted_messages = convert_db_messages_to_langchain(
                    conversation_messages
                )
            else:
                converted_messages = []
            # Make defensive copy to prevent input mutation

            initial_state = State(
                query=user_message,
                messages=converted_messages,
                excluded_ids=excluded_ids,
            )

            self.new_excluded_ids = excluded_ids.copy() if excluded_ids else []

            # Track state changes in instance attributes
            self.rewritten_query = None
            self.response_type = None  # Tracking  response type as a flag
            content_yielded = False

            # Buffer for detecting school logo lines
            line_buffer = ""
            in_school_logo_line = False
            inside_program_section = False
            preamble_buffer = ""
            marker = "----program start----"

            # Stream events from whichever node executes based on routing
            async for event in self.graph.astream_events(initial_state, version="v1"):
                # Capture streaming from whichever endpoint node runs
                if event["event"] == "on_chat_model_stream":
                    node_name = event["metadata"].get("langgraph_node")

                    if node_name in STREAMING_NODES:
                        # send metadata BEFORE first chunk
                        if self.response_type is None:
                            self.response_type = (
                                "programs" if node_name == "sg_bot" else "text"
                            )

                            # Yield early metadata event
                            early_metadata = {
                                "type": "metadata",
                                "response_type": self.response_type,
                            }
                            yield early_metadata

                        # then we stream the chunk
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            content_yielded = True
                            if self.response_type == "programs":
                                if not inside_program_section:
                                    preamble_buffer += chunk.content

                                    idx = preamble_buffer.find(marker)
                                    if idx == -1:
                                        yield chunk.content
                                    else:

                                        yield marker + "\n"
                                        after_marker = preamble_buffer[
                                            idx + len(marker) :
                                        ]
                                        line_buffer += after_marker
                                        preamble_buffer = ""
                                        inside_program_section = True

                                if inside_program_section:
                                    line_buffer += chunk.content

                                    if (
                                        "school logo" in line_buffer.lower()
                                        and not in_school_logo_line
                                    ):
                                        in_school_logo_line = True

                                    # If we're in a school logo line and hit newline, extract it
                                    if in_school_logo_line and "\n" in line_buffer:
                                        import re

                                        match = re.search(
                                            r"school logo\s*:\s*(https?://[^\s\n]+)",
                                            line_buffer,
                                            re.IGNORECASE,
                                        )
                                        if match:
                                            school_logo_url = match.group(1)
                                            logo_metadata = {
                                                "type": "school_logo",
                                                "school_logo": school_logo_url,
                                            }
                                            yield logo_metadata
                                            yield json.dumps(logo_metadata) + "\n"

                                        # Clear the line buffer (don't yield the school logo line as text)
                                        line_buffer = ""
                                        in_school_logo_line = False

                                    # Check for program link lines and extract them
                                    elif (
                                        "program link" in line_buffer.lower()
                                        and "\n" in line_buffer
                                    ):
                                        import re

                                        match = re.search(
                                            r"program link\s*:\s*(https?://[^\s\n]+)",
                                            line_buffer,
                                            re.IGNORECASE,
                                        )
                                        if match:
                                            program_link_url = match.group(1)
                                            program_metadata = {
                                                "type": "program_link",
                                                "program_link": program_link_url,
                                            }
                                            yield program_metadata
                                            yield json.dumps(program_metadata) + "\n"

                                        # Clear the line buffer
                                        line_buffer = ""

                                    # If we're NOT in a school logo line and no special line detected, yield buffered text when we hit a newline
                                    elif (
                                        not in_school_logo_line
                                        and "program link" not in line_buffer.lower()
                                        and "\n" in line_buffer
                                    ):
                                        # Yield the buffered content (program textual lines)
                                        yield line_buffer
                                        line_buffer = ""
                            else:
                                # For non-program responses, stream normally
                                yield chunk.content

                # Capture state changes for tracking
                elif event["event"] == "on_chain_end" and event["metadata"].get(
                    "langgraph_node"
                ):
                    node_data = event["data"].get("output", {})
                    if isinstance(node_data, dict):
                        if "excluded_ids" in node_data:
                            self.new_excluded_ids.extend(node_data["excluded_ids"])
                        if "rewritten_query" in node_data:
                            self.rewritten_query = node_data["rewritten_query"]

            # Flush any remaining buffer
            if line_buffer and not in_school_logo_line:
                yield line_buffer

            # Store final metadata in instance attributes (don't yield)
            self.stream_completed = content_yielded

            # Send final metadata with run_id BEFORE completion marker
            if content_yielded:
                final_metadata = {
                    "type": "metadata",
                    "run_id": self.current_run_id,
                    "rewritten_query": self.rewritten_query,
                }
                yield final_metadata

                # Then yield completion marker
                yield {"__stream_complete__": True}

        except Exception as e:
            print(f"ERROR in stream_workflow: {str(e)}")
            print(f"user_message: {repr(user_message)}")
            print(f"type: {type(user_message)}")
            raise e

    def get_stream_metadata(self):
        metadata = {
            "completed": getattr(self, "stream_completed", False),
            "run_id": self.current_run_id,
            "rewritten_query": self.rewritten_query,
            "excluded_ids": self.new_excluded_ids,
            "response_type": getattr(
                self, "response_type", "text"
            ),  # added response type
        }

        print(f"DEBUG get_stream_metadata returning:")
        print(f"completed: {metadata['completed']}")
        print(f"excluded_ids: {metadata['excluded_ids']}")
        print(f"rewritten_query: {metadata['rewritten_query']}")
        print(
            f"response_type: {metadata['response_type']}"
        )  # added response type for debugging

        return metadata


bot = WorkFlow()
