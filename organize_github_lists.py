import json
import subprocess
import time

with open('starred_rest.json') as f:
    repos = json.load(f)

categories = [
    {
        "name": "🤖 MCP & AI Agents",
        "desc": "Model Context Protocol servers, autonomous agent frameworks, and agentic integrations",
        "keywords": ["mcp", "model-context-protocol", "agent", "paperclip", "serena", "mempalace", "conductor", "gemini-cli"]
    },
    {
        "name": "🧠 AI, LLM & Machine Learning",
        "desc": "Frontier models, fine-tuning, RAG, PyTorch, local inference engines, and neural networks",
        "keywords": ["llm", "ai", "gpt", "rag", "pytorch", "deepseek", "gemma", "llama", "diffusion", "fine-tuning", "vlm", "transformers", "moe", "quantization", "attention"]
    },
    {
        "name": "⚡ DevOps, Linux & Cloud",
        "desc": "Self-hosted services, Linux tools, Docker containers, database engines, and networking",
        "keywords": ["docker", "kubernetes", "linux", "arch", "redis", "postgresql", "pgdog", "quickemu", "selfhosted", "awesome-selfhosted", "server", "ci-cd", "cloud"]
    },
    {
        "name": "🎨 Frontend & Creative Tech",
        "desc": "UI frameworks, design tools, video generation, web specs, and modern editors",
        "keywords": ["react", "next", "vue", "tailwind", "penpot", "remotion", "zed", "ui", "frontend", "web", "css"]
    },
    {
        "name": "🎮 Gaming, Audio & Multimedia",
        "desc": "Game servers, modding tools, speech synthesis, and open-source video editors",
        "keywords": ["rimworld", "fs25", "ls25", "game", "mod", "opencut", "vibevoice", "tts", "audio", "sound"]
    },
    {
        "name": "🧰 DevTools & Resources",
        "desc": "Awesome lists, Python frameworks, CLI search engines, and developer references",
        "keywords": []
    }
]

def classify_repo(repo):
    name = repo['full_name'].lower()
    desc = (repo.get('description') or '').lower()
    topics = [t.lower() for t in repo.get('topics', [])]
    text = f"{name} {desc} {' '.join(topics)}"

    if any(k in text for k in ['mcp', 'model-context-protocol', 'paperclip', 'serena', 'mempalace', 'conductor', 'gemini-cli']):
        return categories[0]['name']
    if any(k in text for k in ['llm', 'ai', 'gpt', 'rag', 'pytorch', 'deepseek', 'gemma', 'llama', 'diffusion', 'fine-tuning', 'vlm', 'transformers', 'moe', 'quantization', 'attention', 'neural']):
        return categories[1]['name']
    if any(k in text for k in ['docker', 'kubernetes', 'linux', 'arch', 'redis', 'postgresql', 'pgdog', 'quickemu', 'selfhosted', 'awesome-selfhosted', 'server', 'ci-cd', 'cloud']):
        return categories[2]['name']
    if any(k in text for k in ['react', 'next', 'vue', 'tailwind', 'penpot', 'remotion', 'zed', 'ui', 'frontend', 'web']):
        return categories[3]['name']
    if any(k in text for k in ['rimworld', 'fs25', 'ls25', 'game', 'mod', 'opencut', 'vibevoice', 'tts', 'audio', 'sound']):
        return categories[4]['name']
    return categories[5]['name']

print("🔍 Step 1: Querying existing user lists...")
query_lists = """
query {
  viewer {
    lists(first: 50) {
      nodes {
        id
        name
      }
    }
  }
}
"""
res = subprocess.run(["gh", "api", "graphql", "-f", f"query={query_lists}"], capture_output=True, text=True)
existing_lists = {}
try:
    data = json.loads(res.stdout)
    nodes = data.get("data", {}).get("viewer", {}).get("lists", {}).get("nodes", [])
    for n in nodes:
        existing_lists[n['name']] = n['id']
except Exception as e:
    pass

create_list_mutation = """
mutation($name: String!, $desc: String) {
  createUserList(input: {name: $name, description: $desc}) {
    list {
      id
      name
    }
  }
}
"""

print("🚀 Step 2: Creating GitHub Star Lists...")
for cat in categories:
    name = cat['name']
    desc = cat['desc']
    if name not in existing_lists:
        cmd = [
            "gh", "api", "graphql",
            "-f", f"query={create_list_mutation}",
            "-f", f"name={name}",
            "-f", f"desc={desc}"
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        try:
            res_json = json.loads(r.stdout)
            if "errors" in res_json:
                print(f"❌ Error creating list '{name}': {res_json['errors'][0]['message']}")
            else:
                list_id = res_json['data']['createUserList']['list']['id']
                existing_lists[name] = list_id
                print(f"✅ Created list: {name} ({list_id})")
        except Exception as ex:
            print("Failed response:", r.stdout)
    else:
        print(f"ℹ️ List already exists: {name}")

# Fetch GraphQL Node IDs for repositories
print("\n🔗 Step 3: Resolving GraphQL IDs for repositories...")
repo_ids = {}

# Query in chunks of 50
for i in range(0, len(repos), 50):
    chunk = repos[i:i+50]
    query_body = ""
    for idx, r in enumerate(chunk):
        owner, repo_name = r['full_name'].split('/')
        # replace hyphen for alias
        alias = f"repo_{idx}"
        query_body += f'{alias}: repository(owner: "{owner}", name: "{repo_name}") {{ id nameWithOwner }}\n'
    
    q = f"query {{\n{query_body}\n}}"
    r = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}"], capture_output=True, text=True)
    try:
        res_json = json.loads(r.stdout)
        if "data" in res_json and res_json['data']:
            for k, v in res_json['data'].items():
                if v and "id" in v:
                    repo_ids[v['nameWithOwner']] = v['id']
    except Exception as ex:
        print("Error resolving chunk:", ex)

print(f"Resolved {len(repo_ids)} repository IDs.")

# Assign repos to lists
assign_mutation = """
mutation($itemId: ID!, $listIds: [ID!]!) {
  updateUserListsForItem(input: {itemId: $itemId, listIds: $listIds}) {
    clientMutationId
  }
}
"""

print("\n🏷️ Step 4: Adding starred repos to lists...")
added_count = 0
for r in repos:
    full_name = r['full_name']
    target_cat = classify_repo(r)
    list_id = existing_lists.get(target_cat)
    repo_id = repo_ids.get(full_name)

    if list_id and repo_id:
        cmd = [
            "gh", "api", "graphql",
            "-f", f"query={assign_mutation}",
            "-f", f"itemId={repo_id}",
            "-f", f"listIds[]={list_id}"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if "errors" in res.stdout:
            pass
        else:
            added_count += 1
            print(f"  [+] Added {full_name} ➔ {target_cat}")

print(f"\n🎉 Done! Processed {added_count} repositories into GitHub Star Lists.")

