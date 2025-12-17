import json
import hashlib
import os
import sys
import argparse
import shutil
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from full_data_pipeline import run_full_pipeline
from create_chroma_documents import ChromaDocumentCreator

from app.core.retrievers.child_parent_splitter import ChildParentSplitter


class SmartPipelineRunner:
    def __init__(self, force_run=False):
        self.force_run = force_run
        # Use absolute paths for GitHub Actions compatibility
        self.data_dir = project_root / "data"
        self.fingerprint_file = self.data_dir / "raw" / "programs_fingerprint.json"
        self.programs_file = self.data_dir / "programs" / "programs.json"
        self.result_file = (
            project_root / "pipeline_result.json"
        )  # Save to root directory
        self.vector_store_path = self.data_dir / "vector_store" / "combined_collections"

    def generate_fingerprint(self, file_path):
        """Generate SHA256 hash of file content"""
        file_path = Path(file_path)
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            return hashlib.sha256(content.encode()).hexdigest()

    def load_previous_fingerprint(self):
        """Load the previous fingerprint"""
        if self.fingerprint_file.exists():
            try:
                with open(self.fingerprint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("fingerprint")
            except (json.JSONDecodeError, FileNotFoundError):
                return None
        return None

    def save_fingerprint(self, fingerprint, stats):
        """Save the current fingerprint with metadata"""
        fingerprint_data = {
            "fingerprint": fingerprint,
            "last_updated": datetime.now().isoformat(),
            "stats": stats,
        }

        self.fingerprint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.fingerprint_file, "w", encoding="utf-8") as f:
            json.dump(fingerprint_data, f, indent=2, ensure_ascii=False)

    def save_result(self, result):
        """Save pipeline result to root directory"""
        # Save to root directory
        with open(self.result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def clean_vector_store(self):
        """Delete the combined_collections vector store if it exists"""
        if self.vector_store_path.exists():
            try:
                shutil.rmtree(self.vector_store_path, ignore_errors=True)
                print(f"Deleted existing vector store: {self.vector_store_path}")
            except Exception as e:
                print(f" Warning: Could not delete vector store: {e}")
        else:
            print(f"Vector store not found (will be created fresh)")

    def get_program_count(self):
        """Count programs in programs.json"""
        try:
            with open(self.programs_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0

    def run(self):
        """Main pipeline runner"""
        print("\n" + "=" * 70)
        print("🚀 SMART PIPELINE RUNNER")
        print("=" * 70 + "\n")

        try:
            # Step 1-8: Always run full data pipeline (API → programs.json)
            print(" Running data processing pipeline (Steps 1-8)...")
            print("-" * 70)
            run_full_pipeline()  # Returns None
            program_count = self.get_program_count()
            print(f"✅ Pipeline complete - {program_count} programs processed\n")

            # Generate fingerprint from programs.json
            print("🔍 Generating fingerprint from programs.json...")
            current_fingerprint = self.generate_fingerprint(self.programs_file)
            print(f"   Current: {current_fingerprint[:16]}...")

            # Load previous fingerprint
            previous_fingerprint = self.load_previous_fingerprint()
            print(
                f"   Previous: {(previous_fingerprint[:16] + '...') if previous_fingerprint else 'None'}\n"
            )

            # Compare fingerprints
            if not self.force_run and current_fingerprint == previous_fingerprint:
                print(" No changes detected in programs.json")
                print(" Skipping vector store creation\n")

                stats = {"programs_processed": program_count}
                result = {
                    "status": "skipped",
                    "reason": "no_changes",
                    "timestamp": datetime.now().isoformat(),
                    "stats": stats,
                }
                self.save_result(result)
                return result

            # Changes detected
            print("Changes detected:")
            if not previous_fingerprint:
                print("   - First run, no previous fingerprint")
            elif self.force_run:
                print("   -  Force run enabled")
            else:
                print("   - programs.json has changed")
            print()

            # Step 9: Create ChromaDB documents
            print(" Step 9: Creating ChromaDB documents...")
            creator = ChromaDocumentCreator("programs/programs.json")
            creator.save_documents_json("chroma_documents/chroma_documents.json")
            print("✅ ChromaDB documents created\n")

            # Step 10: Run child-parent splitter and create vector stores
            print("📝 Step 10: Creating vector stores...")
            self.clean_vector_store()

            splitter = ChildParentSplitter(
                str(self.data_dir / "chroma_documents" / "chroma_documents.json"),
                "## 📅 Detailed Program Information",
            )
            splitter.create_child_documents()
            splitter.save_parent_documents(
                str(self.data_dir / "parents" / "parent_documents.json")
            )

            programs_coll, spec_coll = splitter.create_vectorstore(
                persist_directory=str(self.vector_store_path)
            )

            print(f"✅ Vector stores created:")
            print(
                f"   - Programs collection: {len(programs_coll.get()['ids'])} documents"
            )
            print(
                f"   - Specializations collection: {len(spec_coll.get()['ids'])} documents\n"
            )

            # Save fingerprint and results
            stats = {
                "programs_processed": program_count,
                "child_documents": len(programs_coll.get()["ids"]),
                "specialization_documents": len(spec_coll.get()["ids"]),
            }

            self.save_fingerprint(current_fingerprint, stats)

            result = {
                "status": "completed",
                "stats": stats,
                "timestamp": datetime.now().isoformat(),
                "force_run": self.force_run,
            }
            self.save_result(result)

            print("=" * 70)
            print("✅ PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 70 + "\n")

            return result

        except Exception as e:
            print(f"\n Pipeline failed: {str(e)}")
            import traceback

            traceback.print_exc()

            result = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.save_result(result)
            return result


def main():
    parser = argparse.ArgumentParser(description="Smart Data Pipeline Runner")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force run pipeline even if no changes detected",
    )

    args = parser.parse_args()

    runner = SmartPipelineRunner(force_run=args.force)
    result = runner.run()

    # Exit with 0 only on success, 1 otherwise
    sys.exit(result["status"] != "completed")


if __name__ == "__main__":
    main()
