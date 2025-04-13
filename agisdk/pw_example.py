import os
import time
import playwright.sync_api

# Global Playwright instance
_PLAYWRIGHT = None

def get_playwright():
    """Get or create a global Playwright instance (singleton pattern)."""
    global _PLAYWRIGHT
    if not _PLAYWRIGHT:
        _PLAYWRIGHT = playwright.sync_api.sync_playwright().start()
    return _PLAYWRIGHT


def main():
    # Browser configuration
    viewport = {"width": 1280, "height": 720}
    slow_mo = 100  # Slow down operations by 100ms
    timeout = 30000  # Default timeout in ms
    headless = False  # Set to True for headless mode
    
    # Get Playwright instance
    pw = get_playwright()
    
    # Launch browser (standard way)
    browser = pw.chromium.launch(
        headless=headless,
        slow_mo=slow_mo,
    )
    
    # Create context
    context = browser.new_context(
        viewport=viewport,
    )
    
    # Set default timeout
    context.set_default_timeout(timeout)
    
    # Add page tracking (simplified from original)
    context.expose_binding(
        "page_activated", 
        lambda source: print(f"Page activated: {source['page'].url}")
    )
    
    # Add initialization script for tracking
    context.add_init_script("""
        window.page_activated();
        window.addEventListener("focus", () => {window.page_activated();});
    """)
    
    # Create a new page (main page)
    page = context.new_page()
    
    # Create a background page (as in WebClones)
    background_page = context.new_page()
    
    # Example task setup (similar to AbstractWebCloneTask.setup)
    task_id = "example-task"
    run_id = "0"
    base_url = "https://example.com"  # Replace with actual URL
    
    # Load config in background page
    config_url = f"{base_url}/config?run_id={run_id}&task_id={task_id}"
    try:
        background_page.goto(config_url)
        background_page.wait_for_load_state("networkidle")
    except Exception as e:
        print(f"Error loading config: {e}")
    
    # Ensure main page stays focused
    page.bring_to_front()
    
    # Navigate main page to starting URL
    page.goto(base_url)
    page.wait_for_load_state("domcontentloaded")
    
    # Wait a bit to see the page
    print("Browser opened, press Ctrl+C to exit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing browser...")
    
    # Cleanup
    background_page.close()
    page.close()
    context.close()
    browser.close()
    
    # Note: In a real application, we might want to clean up the global Playwright instance
    # This is often done on application exit to free resources
    # global _PLAYWRIGHT
    # if _PLAYWRIGHT:
    #     _PLAYWRIGHT.stop()
    #     _PLAYWRIGHT = None

if __name__ == "__main__":
    main()