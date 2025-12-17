import json

chroma_documents_programs = "data/chroma_documents/chroma_documents_programs.json"
ge_output = "data/chroma_documents/chroma_documents_ge.json"
es_output = "data/chroma_documents/chroma_documents_es.json"

def split_school_types():
    with open(chroma_documents_programs, "r", encoding= "utf-8") as f:
        programs = json.load(f)
        
    print(f"loaded {len(programs)} programs")
    
    ge = []
    es = []
    
    for program in programs:
        metadata = program.get("metadata", {})
        school_type = metadata.get("school_type", "")
        if school_type == "Grande Ecole":
            ge.append(program)
        if school_type == "Ecole Spécialisée":
            es.append(program)
    
    
    print(f"Saved {len(ge)} Grand Ecole programs")
    with open(ge_output, "w", encoding="utf-8") as f:
        json.dump(ge, f, ensure_ascii=False, indent = 2)
    print(f"Saved {len(es)} Ecole Specialise programs")
    with open(es_output, "w", encoding="utf-8") as f:
        json.dump(es, f, ensure_ascii=False, indent = 2)
    
if __name__ == "__main__":
    split_school_types()