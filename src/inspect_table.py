#!/usr/bin/env python3
"""Quick script to inspect the AJAX form structure."""
import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://quotes.toscrape.com/search.aspx')
        await page.wait_for_timeout(2000)
        
        # Get form structure
        print("Form selects:")
        author_select = await page.query_selector('select#author')
        tag_select = await page.query_selector('select#tag')
        
        if author_select:
            author_count = await author_select.evaluate('(el) => el.options.length')
            print(f"Author select: {author_count} options")
            
            # Get first few author options
            authors = await author_select.evaluate('''
                (el) => Array.from(el.options).slice(0, 5).map(opt => ({value: opt.value, text: opt.text}))
            ''')
            print(f"Sample authors: {authors}")
        
        if tag_select:
            tag_count = await tag_select.evaluate('(el) => el.options.length')
            print(f"\nTag select: {tag_count} options")
            
            # Get first few tag options
            tags = await tag_select.evaluate('''
                (el) => Array.from(el.options).slice(0, 5).map(opt => ({value: opt.value, text: opt.text}))
            ''')
            print(f"Sample tags: {tags}")
        
        # Check if there's a submit button
        submit_btn = await page.query_selector('input[type="submit"]')
        if submit_btn:
            value = await submit_btn.get_attribute('value')
            print(f"\nSubmit button found: {value}")
        
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
