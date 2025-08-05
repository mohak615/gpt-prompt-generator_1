import json
import re
import time
import os
import openai
from scraper import scrape_business_info_with_ai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
def print_banner():
    """Print a beautiful banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🚀 GPT PROMPT GENERATOR                   ║
║                                                              ║
║  Professional Business Data Scraper & Prompt Builder        ║
║  Extract comprehensive business info and create AI prompts  ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_progress(message, delay=0.5):
    """Print progress message with animation"""
    print(f"⏳ {message}", end="", flush=True)
    time.sleep(delay)
    print(" ✅")

def test_gpt_response(final_prompt, model="gpt-3.5-turbo"):
    """Test GPT API with the generated prompt"""
    print(f"\n🤖 TESTING GPT API RESPONSE")
    print("=" * 50)
    print(f"📡 Model: {model}")
    print(f"📝 Prompt Length: {len(final_prompt)} characters")
    
    try:
        # Configure OpenAI
        openai.api_key = OPENAI_API_KEY
        
        # Create a test prompt
        test_prompt = f"""
Based on the following business information, provide a comprehensive analysis and suggestions:

{final_prompt}

Please provide:
1. Business Overview (2-3 sentences)
2. Key Strengths (3-4 points)
3. Marketing Suggestions (3-4 ideas)
4. Potential Improvements (2-3 suggestions)
5. Target Audience Analysis (1-2 sentences)

Format your response professionally with clear sections.
"""
        
        print_progress("Sending request to GPT API")
        
        # Make API call
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional business analyst and marketing consultant. Provide clear, actionable insights based on business information."},
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        gpt_response = response.choices[0].message.content
        
        print_progress("Received response from GPT")
        
        # Display the response
        print(f"\n🎯 GPT API RESPONSE:")
        print("=" * 60)
        print(gpt_response)
        print("=" * 60)
        
        # Save GPT response
        gpt_output_file = "gpt_response.txt"
        with open(gpt_output_file, 'w', encoding='utf-8') as f:
            f.write(f"Original Prompt:\n{final_prompt}\n\n")
            f.write(f"GPT Response:\n{gpt_response}")
        
        print(f"\n💾 GPT response saved to: {gpt_output_file}")
        
        # Show response stats
        response_tokens = response.usage.total_tokens
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        print(f"\n📊 API USAGE STATS:")
        print(f"   • Total Tokens: {response_tokens}")
        print(f"   • Prompt Tokens: {prompt_tokens}")
        print(f"   • Response Tokens: {completion_tokens}")
        
        return True, gpt_response
        
    except Exception as e:
        print(f"❌ GPT API Error: {e}")
        print("💡 Possible issues:")
        print("   • API key might be invalid")
        print("   • Network connection issues")
        print("   • OpenAI service might be down")
        return False, None

def load_template(template_file="prompt_template.txt"):
    """Load the prompt template from file"""
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: Template file '{template_file}' not found.")
        print("💡 Please ensure 'prompt_template.txt' exists in the current directory.")
        return None
    except Exception as e:
        print(f"❌ Error reading template file: {e}")
        return None

def map_scraped_data_to_template(scraped_data):
    """Map scraped data fields to template placeholders"""
    mapping = {
        # Basic Info
        "{{company_name}}": scraped_data.get("company_name", "Not available"),
        "{{address}}": scraped_data.get("address", "Not available"),
        "{{phone_number}}": scraped_data.get("phone_number", "Not available"),
        "{{email}}": scraped_data.get("email", "Not available"),
        "{{website}}": scraped_data.get("website_url", "Not available"),
        "{{business_hours}}": scraped_data.get("business_hours", "Not available"),
        "{{timezone}}": scraped_data.get("timezone", "Not available"),
        
        # Services
        "{{services}}": scraped_data.get("services_list", "Not available"),
        "{{service_descriptions}}": scraped_data.get("service_descriptions", "Not available"),
        "{{pricing}}": scraped_data.get("pricing", "Not available"),
        "{{duration}}": scraped_data.get("duration", "Not available"),
        "{{booking_links}}": scraped_data.get("booking_links", "Not available"),
        "{{service_areas}}": scraped_data.get("service_areas", "Not available"),
        
        # Payments & Policies
        "{{payment_methods}}": scraped_data.get("payment_methods", "Not available"),
        "{{financing}}": scraped_data.get("financing_plans", "Not available"),
        "{{refund_policy}}": scraped_data.get("refund_policy", "Not available"),
        
        # Team Information
        "{{team}}": scraped_data.get("staff_names", "Not available"),
        "{{bios}}": scraped_data.get("staff_titles", "Not available"),  # Using staff_titles as bios
        "{{team_photos}}": scraped_data.get("staff_photos", "Not available"),
        
        # Social Media
        "{{facebook}}": scraped_data.get("facebook_url", "Not available"),
        "{{instagram}}": scraped_data.get("instagram_url", "Not available"),
        "{{linkedin}}": scraped_data.get("linkedin_url", "Not available"),
        "{{other_socials}}": scraped_data.get("social_handles", "Not available"),
        
        # Reviews / Testimonials
        "{{testimonials}}": scraped_data.get("testimonials", "Not available"),
        
        # Policies & Legal
        "{{privacy_policy}}": scraped_data.get("privacy_policy", "Not available"),
        "{{refund_policy}}": scraped_data.get("refund_policy", "Not available"),
        "{{terms}}": scraped_data.get("terms_of_service", "Not available"),
        "{{licenses}}": scraped_data.get("licenses_certifications", "Not available"),
        
        # Brand & Philosophy
        "{{tagline}}": scraped_data.get("tagline", "Not available"),
        "{{mission_statement}}": scraped_data.get("mission_statement", "Not available"),
        "{{tone}}": scraped_data.get("communication_style", "Not available"),
    }
    return mapping

def replace_placeholders(template, data_mapping):
    """Replace all placeholders in the template with actual data"""
    result = template
    for placeholder, value in data_mapping.items():
        result = result.replace(placeholder, str(value))
    return result

def save_final_prompt(final_prompt, output_file="final_prompt.txt"):
    """Save the final prompt to a file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_prompt)
        
        # Get file size
        file_size = os.path.getsize(output_file)
        file_size_kb = file_size / 1024
        
        print(f"✅ Final prompt saved to '{output_file}'")
        print(f"📊 File size: {file_size_kb:.1f} KB")
        return True
    except Exception as e:
        print(f"❌ Error saving final prompt: {e}")
        return False

def print_data_summary(scraped_data):
    """Print a summary of scraped data"""
    print("\n📋 DATA EXTRACTION SUMMARY:")
    print("=" * 50)
    
    # Basic Info
    print("🏢 BASIC INFORMATION:")
    print(f"   • Company: {scraped_data.get('company_name', 'Not found')}")
    print(f"   • Address: {scraped_data.get('address', 'Not found')}")
    print(f"   • Phone: {scraped_data.get('phone_number', 'Not found')}")
    print(f"   • Email: {scraped_data.get('email', 'Not found')}")
    
    # Services
    services = scraped_data.get('services_list', 'Not found')
    if services != 'Not found':
        print(f"\n🛠️  SERVICES FOUND: {len(services.split(',')) if ',' in services else 1} service(s)")
        print(f"   • {services}")
    
    # Pricing
    pricing = scraped_data.get('pricing', 'Not found')
    if pricing != 'Not found':
        print(f"\n💰 PRICING INFORMATION:")
        print(f"   • {pricing}")
    
    # Social Media
    social_count = 0
    if scraped_data.get('facebook_url') != 'Not available': social_count += 1
    if scraped_data.get('instagram_url') != 'Not available': social_count += 1
    if scraped_data.get('linkedin_url') != 'Not available': social_count += 1
    
    print(f"\n📱 SOCIAL MEDIA: {social_count} platform(s) found")
    
    print("=" * 50)

def generate_prompt_from_url(url, template_file="prompt_template.txt", output_file="final_prompt.txt"):
    """Main function to generate prompt from URL"""
    print(f"\n🎯 TARGET WEBSITE: {url}")
    print("=" * 60)
    
    # Step 1: Scrape business data
    print_progress("Initializing web scraper")
    print_progress("Connecting to website")
    
    scraped_data = scrape_business_info_with_ai(url)
    if not scraped_data:
        print("❌ Failed to scrape data from the website")
        print("💡 Possible reasons:")
        print("   • Website might be blocking automated access")
        print("   • URL might be incorrect")
        print("   • Network connection issues")
        return False
    
    print_progress("Extracting business information")
    print_progress("Processing data with AI")
    
    # Step 2: Load template
    print_progress("Loading prompt template")
    template = load_template(template_file)
    if not template:
        return False
    
    # Step 3: Map data to template placeholders
    print_progress("Mapping data to template")
    data_mapping = map_scraped_data_to_template(scraped_data)
    
    # Step 4: Replace placeholders
    print_progress("Replacing placeholders")
    final_prompt = replace_placeholders(template, data_mapping)
    
    # Step 5: Save final prompt
    print_progress("Saving final prompt")
    success = save_final_prompt(final_prompt, output_file)
    
    if success:
        # Print data summary
        print_data_summary(scraped_data)
        
        print("\n🎉 SUCCESS! Your GPT prompt is ready!")
        print("=" * 60)
        print(f"📄 Output file: {output_file}")
        print(f"🔗 Original URL: {url}")
        
        print("\n📋 FINAL PROMPT PREVIEW:")
        print("-" * 60)
        preview = final_prompt[:800] + "..." if len(final_prompt) > 800 else final_prompt
        print(preview)
        print("-" * 60)
        
        print("\n💡 NEXT STEPS:")
        print("   1. Open 'final_prompt.txt' to see the complete prompt")
        print("   2. Copy the content and use it with any AI model")
        print("   3. The prompt contains comprehensive business information")
        
        print("\n⭐ FEATURES EXTRACTED:")
        print("   ✅ Company information & contact details")
        print("   ✅ Services & pricing information")
        print("   ✅ Business hours & policies")
        print("   ✅ Social media links")
        print("   ✅ Team information")
        print("   ✅ Legal policies & certifications")
        print("   ✅ Brand messaging & tone")
        
        # Step 6: Test GPT API Response
        print(f"\n🤖 GPT API TESTING")
        print("=" * 40)
        test_choice = input("Would you like to test the prompt with GPT API? (y/n): ").strip().lower()
        
        if test_choice in ['y', 'yes', 'haan', 'h']:
            test_success, gpt_response = test_gpt_response(final_prompt)
            if test_success:
                print(f"\n🎊 COMPLETE SUCCESS!")
                print("=" * 40)
                print("✅ Data scraped successfully")
                print("✅ Prompt generated successfully") 
                print("✅ GPT API test completed")
                print("✅ All files saved")
            else:
                print(f"\n⚠️  PARTIAL SUCCESS")
                print("=" * 40)
                print("✅ Data scraped successfully")
                print("✅ Prompt generated successfully")
                print("❌ GPT API test failed")
        else:
            print(f"\n✅ PROMPT GENERATION COMPLETE!")
            print("=" * 40)
            print("✅ Data scraped successfully")
            print("✅ Prompt generated successfully")
            print("⏭️  GPT API test skipped")
    
    return success

def get_user_input():
    """Get URL input with validation"""
    print("\n🌐 ENTER BUSINESS WEBSITE URL")
    print("=" * 40)
    print("💡 Examples:")
    print("   • https://www.example.com")
    print("   • https://business-name.com")
    print("   • https://www.restaurant.com")
    print()
    
    while True:
        url = input("🔗 Website URL: ").strip()
        
        if not url:
            print("❌ URL is required. Please enter a valid website URL.")
            continue
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if '.' in url and len(url) > 10:
            return url
        else:
            print("❌ Please enter a valid website URL (e.g., https://example.com)")

if __name__ == "__main__":
    print_banner()
    
    try:
        url = get_user_input()
        generate_prompt_from_url(url)
        
        print("\n" + "=" * 60)
        print("🎊 Thank you for using GPT Prompt Generator!")
        print("   Made with ❤️ for professional business automation")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Process interrupted by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        print("💡 Please try again or check your internet connection")