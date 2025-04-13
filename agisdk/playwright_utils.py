"""
Playwright utilities for the evaluation harness.
"""
from typing import Tuple, Dict, Any, Optional
import time

# Playwright is an optional dependency
try:
    import playwright.sync_api
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Global Playwright instance (singleton)
_PLAYWRIGHT = None

def get_playwright():
    """Get or create a global Playwright instance (singleton pattern)."""
    global _PLAYWRIGHT
    if not _PLAYWRIGHT:
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed. Please install it with: pip install playwright")
        _PLAYWRIGHT = playwright.sync_api.sync_playwright().start()
    return _PLAYWRIGHT

def setup_playwright(task_id: str, base_url: str, run_id: str = "local", 
                     headless: bool = False, slow_mo: int = 100,
                     viewport: Optional[Dict[str, int]] = None, 
                     timeout: int = 30000) -> Tuple[Any, Any, Any, Any]:
    """
    Set up a Playwright environment for a task.
    
    Args:
        task_id: The ID of the task
        base_url: The base URL for the task
        run_id: The run ID for the task (defaults to "local")
        headless: Whether to run the browser in headless mode
        slow_mo: Slow down operations by this amount in ms
        viewport: Viewport dimensions (width and height)
        timeout: Default timeout in ms
        
    Returns:
        Tuple of (browser, context, main_page, background_page)
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError("Playwright is not installed. Please install it with: pip install playwright")
    
    # Default viewport
    if viewport is None:
        viewport = {"width": 1280, "height": 720}
    
    # Get Playwright instance
    pw = get_playwright()
    
    # Launch browser
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
    
    # Add page tracking
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
    main_page = context.new_page()
    
    # Create a background page
    background_page = context.new_page()
    
    # Load config in background page
    config_url = f"{base_url}/config?run_id={run_id}&task_id={task_id}"
    try:
        background_page.goto(config_url)
        background_page.wait_for_load_state("networkidle")
    except Exception as e:
        print(f"Error loading config: {e}")
    
    # Ensure main page stays focused
    main_page.bring_to_front()
    
    # Navigate main page to starting URL
    main_page.goto(base_url)
    main_page.wait_for_load_state("domcontentloaded")
    
    return browser, context, main_page, background_page

def cleanup_playwright(browser, context=None, main_page=None, background_page=None):
    """
    Clean up Playwright resources.
    
    Args:
        browser: The browser instance
        context: The browser context
        main_page: The main page
        background_page: The background page
    """
    try:
        if background_page:
            background_page.close()
        if main_page:
            main_page.close()
        if context:
            context.close()
        if browser:
            browser.close()
    except Exception as e:
        print(f"Error cleaning up Playwright resources: {e}")

def cleanup_global_playwright():
    """Clean up the global Playwright instance."""
    global _PLAYWRIGHT
    if _PLAYWRIGHT:
        try:
            _PLAYWRIGHT.stop()
        except Exception as e:
            print(f"Error stopping global Playwright instance: {e}")
        finally:
            _PLAYWRIGHT = None

def get_finish_json(url, page, timeout=1000):
    """
    Extract JSON data from the finish endpoint.
    This mimics AbstractWebCloneTask.get_finish_json()
    
    Args:
        url: The base URL of the task
        page: The Playwright page object
        timeout: Maximum time to wait for navigation and selectors
        
    Returns:
        Tuple of (environment_state_json, error_message)
    """
    try:
        # Navigate to the finish endpoint
        page.goto(f"{url}/finish", timeout=timeout)
        page.wait_for_load_state("networkidle", timeout=timeout)
        
        # Find the pre element containing JSON data
        pre_element = page.wait_for_selector("pre")
        if pre_element:
            # Extract the text content
            env_state = pre_element.inner_text()
            try:
                # Parse the JSON
                import json
                env_state_json = json.loads(env_state)
                return env_state_json, None
            except json.JSONDecodeError as e:
                error_message = f"Invalid JSON format: {str(e)}"
                return None, error_message
        else:
            return None, "No state data available"
    except Exception as e:
        return None, f"Error retrieving data: {str(e)}"