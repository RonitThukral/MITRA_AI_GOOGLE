from typing import List, Dict
import aiohttp
from config import SERPAPI_KEY, GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID

async def search_serpapi(query: str, num_results: int = 8) -> List[Dict]:
    """Search using SerpApi."""
    print(f"🔍 SerpApi search: {query}")
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": num_results,
            "gl": "in",
            "hl": "en",
            "safe": "active"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=15) as response:
                print(f"SerpApi response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    if data.get("answer_box"):
                        answer = data["answer_box"]
                        snippet = answer.get("answer", "") or answer.get("snippet", "") or answer.get("result", "")
                        if snippet:
                            results.append({
                                "title": f"Direct Answer: {answer.get('title', 'Quick Answer')}",
                                "snippet": snippet,
                                "link": answer.get("link", ""),
                                "source": "Google Answer Box"
                            })
                    
                    if data.get("knowledge_graph"):
                        kg = data["knowledge_graph"]
                        description = kg.get("description", "")
                        if description:
                            results.append({
                                "title": f"Knowledge: {kg.get('title', 'Information')}",
                                "snippet": description,
                                "link": kg.get("website", ""),
                                "source": "Google Knowledge Graph"
                            })
                    
                    for item in data.get("organic_results", []):
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        if title and snippet:
                            results.append({
                                "title": title,
                                "snippet": snippet,
                                "link": item.get("link", ""),
                                "source": "Google Search"
                            })
                    
                    print(f"SerpApi found {len(results)} results")
                    return results[:num_results]
                else:
                    return []
    except Exception as e:
        print(f"SerpApi exception: {e}")
        return []

async def search_google_custom(query: str, num_results: int = 5) -> List[Dict]:
    """Search using Google Custom Search API with official education sites."""
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        print("Google Custom Search credentials missing")
        return []
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_CSE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": f"{query} site:nta.ac.in OR site:josaa.nic.in OR site:mhrd.gov.in OR site:ugc.ac.in",
            "num": min(num_results, 10),
            "gl": "in",
            "hl": "en",
            "safe": "medium",
            "dateRestrict": "y1"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get("items", []):
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        if title and snippet and len(snippet) > 50:
                            results.append({
                                "title": title,
                                "snippet": snippet,
                                "link": item.get("link", ""),
                                "source": "Official Education Sites"
                            })
                    
                    print(f"Google Custom Search found {len(results)} results")
                    return results
                else:
                    print(f"Google Custom Search API error: {response.status}")
                    return []
    except Exception as e:
        print(f"Google Custom Search exception: {e}")
        return []

async def perform_web_search(query: str, num_results: int = 6) -> tuple[List[Dict], str]:
    """Perform web search with prioritization of Google Custom Search."""
    print(f"🌐 Intelligent search for: '{query}'")
    
    results = await search_google_custom(query, num_results)
    if results and len(results) >= 2:
        print(f"✅ Google Custom Search successful: {len(results)} results")
        return results, "Google Custom Search"
    
    print("⚠️ Trying SerpApi for broader search...")
    serp_results = await search_serpapi(query, num_results)
    if serp_results:
        print(f"✅ SerpApi successful: {len(serp_results)} results")
        return serp_results, "SerpApi"
    
    print("❌ All search methods failed")
    return [], "Search unavailable"

def build_optimized_search_query(user_message: str) -> str:
    """Build optimized search queries for better results."""
    message_lower = user_message.lower()
    
    if "jee" in message_lower and ("2025" in message_lower or "date" in message_lower):
        return "JEE Main 2025 exam dates official NTA schedule"
    
    if "neet" in message_lower and ("2025" in message_lower or "date" in message_lower):
        return "NEET 2025 exam date official NTA notification"
        
    if any(term in message_lower for term in ["after 10th", "10th class"]):
        return "career options after 10th class India 2024 2025"
    elif any(term in message_lower for term in ["after 12th", "12th class"]):
        return "career options after 12th India 2024 2025"
    elif "cutoff" in message_lower:
        return f"college cutoff 2024 India admission {user_message}"
    elif "admission" in message_lower:
        return f"college admission process 2024 2025 India {user_message}"
    
    return f"{user_message} India 2024 2025 official"

def should_perform_web_search(message: str, career_mode: bool) -> bool:
    """Detect when a web search is needed."""
    if not career_mode:
        return False
    
    always_search = [
        "date", "2025", "2024", "when", "cutoff", "admission", "latest",
        "current", "fees", "ranking", "eligibility", "notification",
        "result", "exam", "application", "form", "last date"
    ]
    
    search_triggers = [
        "jee", "neet", "clat", "gate", "cat", "mat", "xat",
        "iit", "nit", "iiit", "aiims", "jipmer"
    ]
    
    message_lower = message.lower()
    
    if any(term in message_lower for term in always_search):
        return True
        
    if any(term in message_lower for term in search_triggers):
        return True
        
    if any(phrase in message_lower for phrase in [
        "career option", "what should i", "which course", "best college",
        "how to get", "admission process"
    ]):
        return True
    
    return False