from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse
from collections import deque
import openai
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
def clean_text(text):
    if not text:
        return "Not available"
    if isinstance(text, dict):
        return str(text)
    if not isinstance(text, str):
        return str(text)
    return " ".join(text.split())

def extract_links(page, base_url):
    anchors = page.query_selector_all('a[href]')
    links = set()
    for a in anchors:
        href = a.get_attribute('href')
        if href and not href.startswith('mailto:') and not href.startswith('tel:'):
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.add(full_url.split('#')[0])
    return links

def scrape_and_collect_text(url, max_pages=8):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        visited = set()
        queue = deque([url])
        all_text = []
        pages_crawled = 0
        while queue and pages_crawled < max_pages:
            current_url = queue.popleft()
            if current_url in visited:
                continue
            try:
                page.goto(current_url, timeout=30000)
                page.wait_for_load_state('networkidle', timeout=20000)
            except Exception:
                continue
            visited.add(current_url)
            pages_crawled += 1
            
            # More comprehensive text extraction
            page_text = page.inner_text('body')
            all_text.append(page_text)
            
            links = extract_links(page, url)
            for link in links:
                if link not in visited and any(x in link.lower() for x in ["contact", "about", "footer", "info", "service", "hours", "payment", "team", "staff", "social", "policy", "privacy", "terms"]):
                    queue.append(link)
        browser.close()
        combined = '\n\n'.join(all_text)
        return combined[:8000]  # Increased limit

def extract_with_llm(text):
    prompt = f"""
Extract the following comprehensive business information from the text below. If a field is not found, return 'Not available'. 
IMPORTANT: Be very thorough in extracting pricing information, service durations, and all business details. Look for dollar amounts ($), pricing packages, course durations, and service costs.
Output as JSON with these keys:

Basic Info:
- company_name: Business/company name
- address: Street address, city, state, ZIP
- phone_number: Phone number
- email: Email address (look for contact forms, email links, mailto: links, contact information)
- business_hours: Operating hours (look for "hours", "open", "closed", days of week, time schedules)
- website_url: Website URL

Services:
- services_list: List of services offered (as comma-separated string)
- service_descriptions: Descriptions of services
- pricing: Pricing information (look for dollar amounts, costs, fees, packages)
- duration: Service duration (look for hours, days, weeks, course lengths)
- booking_links: Online booking links (look for "book online", "schedule", "appointment", "reserve", booking forms)
- service_areas: Service areas/cities (look for "serving", "areas", "locations", "cities", "regions")

Payments & Policies:
- payment_methods: Accepted payment methods (look for PacePay, credit cards, cash, financing options)
- financing_plans: Financing options (look for payment plans, tuition assistance, lenders)
- refund_policy: Refund/cancellation policy

Team:
- staff_names: Staff member names
- staff_titles: Job titles/roles

Social Media:
- facebook_url: Facebook URL (look for facebook.com links, Facebook icons, social media links)
- instagram_url: Instagram URL (look for instagram.com links, Instagram icons, social media links)
- linkedin_url: LinkedIn URL (look for linkedin.com links, LinkedIn icons, social media links)

Policies:
- privacy_policy: Privacy policy (look for "privacy policy", "privacy", "data protection")
- terms_of_service: Terms of service (look for "terms", "terms of service", "terms of use")
- licenses_certifications: Licenses/certifications

Branding:
- tagline: Company tagline/slogan (look for slogans, catchphrases, company mottos, short memorable phrases)
- mission_statement: Mission statement

Text:
{text}
"""
    openai.api_key = OPENAI_API_KEY
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert business information extractor. Extract comprehensive business details from web page text with high accuracy. Be thorough and extract all available information including pricing, locations, policies, and business details."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    import json
    try:
        content = response.choices[0].message.content
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            json_str = content[start:end+1]
            result = json.loads(json_str)
            
            # Flatten nested structure
            flattened = {}
            for section in ["Basic Info", "Services", "Payments & Policies", "Team", "Social Media", "Policies", "Branding"]:
                if section in result:
                    flattened.update(result[section])
            
            # Convert arrays to strings and handle dictionaries
            for key, value in flattened.items():
                if isinstance(value, list):
                    flattened[key] = ", ".join(value)
                elif isinstance(value, dict):
                    # Convert dict to readable string
                    dict_items = []
                    for k, v in value.items():
                        dict_items.append(f"{k}: {v}")
                    flattened[key] = "; ".join(dict_items)
            
            return flattened
        else:
            return None
    except Exception as e:
        print("LLM extraction error:", e)
        return None



def scrape_business_info_with_ai(url):
    text = scrape_and_collect_text(url)
    
    # Pure AI Extraction
    ai_result = extract_with_llm(text)
    
    # Ensure all fields exist
    fields = [
        "company_name", "address", "phone_number", "email", "website_url", "business_hours", "timezone",
        "services_list", "service_descriptions", "pricing", "duration", "booking_links", "service_areas",
        "payment_methods", "financing_plans", "refund_policy",
        "staff_names", "staff_titles", "staff_bios", "staff_photos",
        "facebook_url", "instagram_url", "linkedin_url", "social_handles", "promotions", "testimonials",
        "privacy_policy", "terms_of_service", "licenses_certifications",
        "tagline", "mission_statement", "communication_style"
    ]
    
    if not ai_result:
        return {k: "Not available" for k in fields}
    
    # Set website URL and ensure all fields exist
    ai_result['website_url'] = url
    
    for field in fields:
        if field not in ai_result or not ai_result[field]:
            ai_result[field] = "Not available"
    
    return {k: clean_text(ai_result[k]) for k in fields}

if __name__ == "__main__":
    url = input("Enter business website URL: ").strip()
    data = scrape_business_info_with_ai(url)
    if not data:
        print("\nFailed to fetch or parse the website. Please check the URL or your internet connection.")
    else:
        print("\nScraped Data:")
        print("\n=== BASIC INFO ===")
        print(f"Company Name: {data['company_name']}")
        print(f"Address: {data['address']}")
        print(f"Phone Number: {data['phone_number']}")
        print(f"Email: {data['email']}")
        print(f"Website URL: {data['website_url']}")
        print(f"Business Hours: {data['business_hours']}")
        print(f"Timezone: {data['timezone']}")
        
        print("\n=== SERVICES ===")
        print(f"Services List: {data['services_list']}")
        print(f"Service Descriptions: {data['service_descriptions']}")
        print(f"Pricing: {data['pricing']}")
        print(f"Duration: {data['duration']}")
        print(f"Booking Links: {data['booking_links']}")
        print(f"Service Areas: {data['service_areas']}")
        
        print("\n=== PAYMENTS & POLICIES ===")
        print(f"Payment Methods: {data['payment_methods']}")
        print(f"Financing Plans: {data['financing_plans']}")
        print(f"Refund Policy: {data['refund_policy']}")
        
        print("\n=== TEAM ===")
        print(f"Staff Names: {data['staff_names']}")
        print(f"Staff Titles: {data['staff_titles']}")
        print(f"Staff Bios: {data['staff_bios']}")
        print(f"Staff Photos: {data['staff_photos']}")
        
        print("\n=== SOCIAL MEDIA ===")
        print(f"Facebook URL: {data['facebook_url']}")
        print(f"Instagram URL: {data['instagram_url']}")
        print(f"LinkedIn URL: {data['linkedin_url']}")
        print(f"Social Handles: {data['social_handles']}")
        print(f"Promotions: {data['promotions']}")
        print(f"Testimonials: {data['testimonials']}")
        
        print("\n=== POLICIES ===")
        print(f"Privacy Policy: {data['privacy_policy']}")
        print(f"Terms of Service: {data['terms_of_service']}")
        print(f"Licenses/Certifications: {data['licenses_certifications']}")
        
        print("\n=== BRANDING ===")
        print(f"Tagline: {data['tagline']}")
        print(f"Mission Statement: {data['mission_statement']}")
        print(f"Communication Style: {data['communication_style']}")