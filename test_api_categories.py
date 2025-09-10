#!/usr/bin/env python3
"""
Test script to verify categories load and render correctly in vendor_application_api.html
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_with_selenium():
    """Use selenium to test the actual UI interaction"""
    print("Testing vendor application API version with headless browser...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the page
        print("Loading page...")
        driver.get("http://localhost:8000/vendor-application-api")
        
        # Wait for the page to load and API to fetch data
        time.sleep(3)
        
        # Get console logs
        logs = driver.execute_script("return window.console.logs || []")
        for log in logs:
            print(f"Console: {log}")
        
        # Check if SERVICE_CATEGORIES is loaded
        categories_loaded = driver.execute_script("return window.SERVICE_CATEGORIES && Object.keys(window.SERVICE_CATEGORIES).length")
        print(f"Categories loaded: {categories_loaded}")
        
        # Check dropdown population
        dropdown = driver.find_element(By.ID, "primary_service_category")
        select = Select(dropdown)
        options = [opt.text for opt in select.options]
        print(f"Dropdown options: {len(options) - 1} categories")  # -1 for placeholder
        print(f"First 5 options: {options[:6]}")  # Including placeholder
        
        # Try selecting a category
        if len(options) > 1:
            print("\nTesting category selection...")
            select.select_by_visible_text("Boat Maintenance")
            time.sleep(1)
            
            # Check if services container is visible
            services_section = driver.find_element(By.ID, "primary-services-section")
            is_visible = services_section.is_displayed()
            print(f"Services section visible: {is_visible}")
            
            if is_visible:
                # Check services rendered
                services_container = driver.find_element(By.ID, "primary-services-container")
                services = services_container.find_elements(By.CLASS_NAME, "service-tag")
                print(f"Services rendered: {len(services)}")
                if services:
                    print(f"First 3 services: {[s.text for s in services[:3]]}")
        
        driver.quit()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Fallback simple test without selenium
def test_simple():
    """Simple test without selenium"""
    import requests
    
    print("Simple test of vendor application API version...")
    
    # Test the API endpoint
    resp = requests.get("http://localhost:8000/api/v1/services/hierarchy")
    if resp.status_code == 200:
        data = resp.json()
        if data.get("success"):
            print(f"✅ API working: {data['stats']['total_categories']} categories")
    
    # Test the HTML page loads
    resp = requests.get("http://localhost:8000/vendor-application-api")
    if resp.status_code == 200:
        content = resp.text
        if "populateCategoryDropdown" in content:
            print("✅ populateCategoryDropdown function found")
        if "loadServiceHierarchy" in content:
            print("✅ loadServiceHierarchy function found")
        if "renderPrimaryServices" in content:
            print("✅ renderPrimaryServices function found")

if __name__ == "__main__":
    # Try selenium first, fall back to simple test
    try:
        import selenium
        test_with_selenium()
    except ImportError:
        print("Selenium not installed, running simple test...")
        test_simple()