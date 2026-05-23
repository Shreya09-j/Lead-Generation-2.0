#!/usr/bin/env python3

import pandas as pd
import requests
import time
import random
import logging

from playwright.sync_api import sync_playwright


# =========================================================
# CONFIG
# =========================================================

INPUT_CSV = "Perf_Marketing_Agencies_Global.xlsx - France.csv"

ROCKETREACH_API_KEY = "1ea3db2k02cbe757c96f6695ac51c2dc579bdaed"

LINKEDIN_EMAIL = 
LINKEDIN_PASSWORD = 


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s"
)


# =========================================================
# LINKEDIN LOGIN
# =========================================================

def linkedin_login(page):

    page.goto(
        "https://www.linkedin.com/",
        wait_until="domcontentloaded"
    )

    time.sleep(5)

    current_url = page.url

    # already logged in
    if "feed" in current_url:

        logging.info("Already logged into LinkedIn")

        return

    # otherwise login manually
    page.goto(
        "https://www.linkedin.com/login",
        wait_until="domcontentloaded"
    )

    time.sleep(3)

    page.fill("#username", LINKEDIN_EMAIL)

    page.fill("#password", LINKEDIN_PASSWORD)

    page.click("button[type='submit']")

    time.sleep(5)

# =========================================================
# SEARCH PEOPLE
# =========================================================

def search_people(page, company):

    query = f"{company} CEO OR Founder OR CTO"

    search_url = (
        "https://www.linkedin.com/search/results/people/?keywords="
        + query.replace(" ", "%20")
    )

    page.goto(
        search_url,
        wait_until="domcontentloaded"
    )

    time.sleep(random.uniform(3, 5))


# =========================================================
# EXTRACT PERSON
# =========================================================

def extract_person(page):

    cards = page.query_selector_all(
        "div.entity-result"
    )

    for card in cards[:5]:

        try:

            name_element = card.query_selector(
                "span[aria-hidden='true']"
            )

            if not name_element:
                continue

            full_name = (
                name_element.inner_text()
                .strip()
            )

            parts = full_name.split()

            first_name = ""
            last_name = ""

            if len(parts) >= 1:
                first_name = parts[0]

            if len(parts) >= 2:
                last_name = parts[-1]

            return {
                "first_name": first_name,
                "last_name": last_name
            }

        except:
            continue

    return None


# =========================================================
# ROCKETREACH ENRICHMENT
# =========================================================

def enrich_contact(first_name, last_name, company):

    url = "https://api.rocketreach.co/v2/api/person/lookup"

    headers = {
        "Api-Key": "1ea3db2k02cbe757c96f6695ac51c2dc579bdaed"
    }

    params = {
        "name": f"{first_name} {last_name}",
        "current_employer": company
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code != 200:

            logging.info(
                f"RocketReach failed: {response.status_code}"
            )

            return {
                "email": "",
                "phone": ""
            }

        data = response.json()

        email = ""
        phone = ""

        if "professional_emails" in data:

            emails = data["professional_emails"]

            if emails:
                email = emails[0]

        if "phones" in data:

            phones = data["phones"]

            if phones:
                phone = phones[0]

        return {
            "email": email,
            "phone": phone
        }

    except Exception as e:

        logging.info(f"Enrichment failed: {e}")

        return {
            "email": "",
            "phone": ""
        }


# =========================================================
# PROCESS COMPANY
# =========================================================

def process_company(page, company):

    logging.info(f"Processing {company}")

    search_people(page, company)

    person = extract_person(page)

    if not person:

        return {
            "first name": "",
            "last name": "",
            "EMAIL": "",
            "phone number": ""
        }

    first_name = person["first_name"]
    last_name = person["last_name"]

    enriched = enrich_contact(
        first_name,
        last_name,
        company
    )

    return {
        "first name": first_name,
        "last name": last_name,
        "EMAIL": enriched["email"],
        "phone number": enriched["phone"]
    }


# =========================================================
# MAIN
# =========================================================

def main():

    df = pd.read_csv(
        INPUT_CSV,
        dtype=str,
        encoding="utf-8",
        on_bad_lines="skip"
    ).fillna("")

    required_columns = [
        "first name",
        "last name",
        "EMAIL",
        "phone number"
    ]

    for col in required_columns:

        if col not in df.columns:
            df[col] = ""

        df[col] = df[col].astype(str)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        linkedin_login(page)

        for index, row in df.iterrows():

            try:

                company = str(
                    row.get("Company Name", "")
                ).strip()

                if not company:
                    continue

                result = process_company(
                    page,
                    company
                )

                df.at[index, "first name"] = str(result["first name"])
                df.at[index, "last name"] = str(result["last name"])
                df.at[index, "EMAIL"] = str(result["EMAIL"])
                df.at[index, "phone number"] = str(result["phone number"])

                logging.info(f"Updated {company}")

                time.sleep(random.uniform(3, 6))

            except Exception as e:

                logging.info(
                    f"Failed processing {company}: {e}"
                )

                continue

        browser.close()

    # SAVE SAME FILE
    df.to_csv(
        INPUT_CSV,
        index=False
    )

    print("\nDONE")
    print(f"Updated {INPUT_CSV}")


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()