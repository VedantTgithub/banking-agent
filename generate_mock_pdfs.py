"""
generate_mock_pdfs.py
Run this ONCE from your project root to create mock RBI/Basel policy PDFs.
Place the generated PDFs in: rag/docs/

Usage:
    python generate_mock_pdfs.py

Requirements:
    pip install reportlab
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

OUTPUT_DIR = "rag/docs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()

def heading1(text):
    return Paragraph(text, styles["Heading1"])

def heading2(text):
    return Paragraph(text, styles["Heading2"])

def body(text):
    return Paragraph(text, styles["Normal"])

def spacer():
    return Spacer(1, 0.4 * cm)

def build_table(data, col_widths=None):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ══════════════════════════════════════════════════════════════════════════════
# PDF 1 — RBI Master Circular: Loans & Advances
# ══════════════════════════════════════════════════════════════════════════════
def create_rbi_master_circular():
    path = os.path.join(OUTPUT_DIR, "rbi_master_circular_loans.pdf")
    doc  = SimpleDocTemplate(path, pagesize=A4)
    story = []

    story += [
        heading1("Reserve Bank of India"),
        heading1("Master Circular — Loans and Advances"),
        body("RBI/2024-25/01 | DBOD.No.Dir.BC. 13/13.03.00/2024-25"),
        body("Issued: April 1, 2024 | Effective: April 1, 2024"),
        spacer(),
        heading2("1. Introduction"),
        body(
            "This Master Circular consolidates all instructions issued by the Reserve Bank of India "
            "on loans and advances extended by Scheduled Commercial Banks (SCBs). These guidelines "
            "govern prudential norms, eligibility criteria, exposure limits, and reporting requirements "
            "for all categories of retail and corporate lending."
        ),
        spacer(),
        heading2("2. Scope and Applicability"),
        body(
            "These guidelines apply to all Scheduled Commercial Banks including public sector banks, "
            "private sector banks, foreign banks operating in India, small finance banks, and payment "
            "banks where applicable. All loan products — including home loans, personal loans, vehicle "
            "loans, business loans, and gold loans — are covered under this circular."
        ),
        spacer(),
        heading2("3. Loan-to-Value (LTV) Norms"),
        body(
            "Section 3.2 — LTV Ratio for Home Loans: Banks shall adhere to the following Loan-to-Value "
            "ratios for housing loans based on the sanctioned loan amount:"
        ),
        spacer(),
        build_table(
            [
                ["Loan Amount (Home Loan)", "Maximum LTV Ratio", "Risk Weight"],
                ["Up to Rs 30 Lakhs",       "90%",               "35%"],
                ["Above Rs 30 Lakhs up to Rs 75 Lakhs", "80%",   "50%"],
                ["Above Rs 75 Lakhs",        "75%",               "75%"],
            ],
            col_widths=[8*cm, 5*cm, 5*cm]
        ),
        spacer(),
        body(
            "Section 3.3 — LTV for Vehicle Loans: The maximum LTV ratio for vehicle loans shall not "
            "exceed 85% of the on-road price of the vehicle. For commercial vehicles, the LTV cap "
            "is 75%. Banks must obtain adequate insurance on collateral vehicles."
        ),
        spacer(),
        body(
            "Section 3.4 — LTV Breaches: Any sanctioned loan where the LTV ratio exceeds the prescribed "
            "limits shall be treated as a regulatory violation and must be reported to the RBI in the "
            "next quarterly compliance submission. The excess exposure must be covered by additional "
            "collateral or margin money within 30 days of disbursal."
        ),
        spacer(),
        heading2("4. Fixed Obligation to Income Ratio (FOIR)"),
        body(
            "Section 4.1 — FOIR Computation: The Fixed Obligation to Income Ratio (FOIR) is computed "
            "as total fixed monthly obligations (including proposed EMI) divided by net monthly income. "
            "Banks shall ensure FOIR does not exceed the following limits:"
        ),
        spacer(),
        build_table(
            [
                ["Borrower Category",        "FOIR Warning Limit", "FOIR Hard Reject Limit"],
                ["Salaried Employees",        "50%",                "65%"],
                ["Self-Employed Professionals","55%",               "70%"],
                ["Business Owners",           "55%",                "70%"],
                ["Agricultural / Seasonal",   "40%",                "60%"],
            ],
            col_widths=[7*cm, 5*cm, 6*cm]
        ),
        spacer(),
        body(
            "Section 4.2 — High FOIR Applications: Applications where FOIR exceeds the warning limit "
            "must be escalated to a senior credit officer for manual review. Applications exceeding "
            "the hard reject limit shall be declined at the processing stage unless supported by "
            "additional collateral equivalent to at least 150% of the loan amount."
        ),
        spacer(),
        heading2("5. Debt-to-Income Ratio (DTI)"),
        body(
            "Section 5.1 — DTI Norms: The Debt-to-Income ratio represents total annual debt obligations "
            "as a percentage of gross annual income. RBI recommends that banks maintain a portfolio "
            "average DTI of below 40%. For individual borrowers, the DTI at the time of loan sanction "
            "shall not exceed 50% under normal circumstances. Where DTI exceeds 45%, additional "
            "verification of income sources is mandatory."
        ),
        spacer(),
        heading2("6. Loan Tenure Limits"),
        body("Section 6.1 — Maximum Permissible Loan Tenures by Product:"),
        spacer(),
        build_table(
            [
                ["Loan Type",        "Maximum Tenure",  "Notes"],
                ["Home Loan",        "30 Years",         "Including moratorium period"],
                ["Personal Loan",    "7 Years",          "Unsecured; stricter income check required"],
                ["Vehicle Loan",     "7 Years",          "Tied to vehicle's residual life"],
                ["Business Loan",    "15 Years",         "Subject to business vintage verification"],
                ["Gold Loan",        "3 Years",          "Bullet repayment permitted"],
                ["Education Loan",   "15 Years",         "Moratorium for course duration + 1 year"],
            ],
            col_widths=[5*cm, 5*cm, 8*cm]
        ),
        spacer(),
        body(
            "Section 6.2 — Tenure Beyond Limits: Any sanctioning of a loan with tenure beyond the "
            "prescribed maximum must receive explicit written approval from the bank's Credit Committee "
            "and must be flagged in the Bank's credit risk register."
        ),
        spacer(),
        heading2("7. Minimum Credit Score Requirements"),
        body(
            "Section 7.1 — Bureau Score Thresholds: Based on RBI directives and internal risk "
            "management prudence, banks must apply the following minimum CIBIL/bureau score thresholds "
            "before loan sanction:"
        ),
        spacer(),
        build_table(
            [
                ["Loan Type",     "Minimum Bureau Score", "Action if Below Minimum"],
                ["Home Loan",     "650",                   "Refer to Credit Committee"],
                ["Personal Loan", "700",                   "Decline or require co-applicant"],
                ["Vehicle Loan",  "650",                   "Decline or require higher margin"],
                ["Business Loan", "675",                   "Require audited financials"],
                ["Gold Loan",     "No minimum",            "Secured by gold pledge"],
            ],
            col_widths=[5*cm, 6*cm, 7*cm]
        ),
        spacer(),
        body(
            "Section 7.2 — No Credit History: For borrowers with no credit history (NTC — New to Credit), "
            "banks may consider surrogate data including utility bill payment history, bank statement "
            "analysis for 12 months, employer salary certificate, and rental agreement history. "
            "NTC borrowers shall not be sanctioned personal loans above Rs 2 Lakhs without co-applicant."
        ),
        spacer(),
        heading2("8. Unsecured Loan Amount Caps"),
        body(
            "Section 8.1 — Unsecured Personal Loan Cap: For personal loans without any collateral, "
            "the maximum permissible sanction amount per borrower is Rs 25 Lakhs. Any loan above this "
            "threshold must either be secured by adequate collateral or require a co-applicant with "
            "independent income verification. The combined unsecured exposure to a single borrower "
            "across all lenders shall not normally exceed Rs 50 Lakhs."
        ),
        spacer(),
        body(
            "Section 8.2 — Business Loans: Unsecured business loans above Rs 50 Lakhs require "
            "audited financial statements for the past 3 years, GST returns for 12 months, and "
            "bank statements demonstrating business cash flow."
        ),
        spacer(),
        heading2("9. Compliance and Reporting"),
        body(
            "Banks must submit quarterly compliance reports to the RBI detailing: (a) portfolio LTV "
            "distribution, (b) FOIR breach cases, (c) loans sanctioned with bureau scores below the "
            "minimum threshold, and (d) loans with tenures beyond permissible limits. Non-compliance "
            "with these guidelines may attract penalties under Section 47A of the Banking Regulation "
            "Act, 1949."
        ),
    ]

    doc.build(story)
    print(f"Created: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# PDF 2 — RBI KYC Guidelines
# ══════════════════════════════════════════════════════════════════════════════
def create_rbi_kyc_guidelines():
    path = os.path.join(OUTPUT_DIR, "rbi_kyc_guidelines.pdf")
    doc  = SimpleDocTemplate(path, pagesize=A4)
    story = []

    story += [
        heading1("Reserve Bank of India"),
        heading1("Know Your Customer (KYC) Guidelines"),
        body("Master Direction — Know Your Customer (KYC) Direction, 2016 (Updated 2024)"),
        body("RBI/2024-25/KYC/001"),
        spacer(),
        heading2("1. Purpose and Legal Basis"),
        body(
            "These directions are issued by the Reserve Bank of India under Section 35A of the "
            "Banking Regulation Act, 1949, Rule 9 of the Prevention of Money Laundering (Maintenance "
            "of Records) Rules, 2005, and the Prevention of Money Laundering Act, 2002. All Regulated "
            "Entities (REs) must implement robust KYC procedures to prevent money laundering, terrorist "
            "financing, and financial fraud."
        ),
        spacer(),
        heading2("2. Mandatory Identity Documents for Loan Applications"),
        body(
            "Section 2.1 — PAN Card Requirement: Quoting and verification of PAN (Permanent Account "
            "Number) is MANDATORY for all loan applications where the loan amount exceeds Rs 50,000. "
            "This requirement applies to all categories of borrowers including individuals, "
            "partnership firms, companies, and Hindu Undivided Families (HUFs)."
        ),
        spacer(),
        body(
            "Section 2.2 — PAN Validation: Banks must validate PAN against the Income Tax Department's "
            "database using the PAN verification API before loan sanction. A PAN that is invalid, "
            "inactive, or belonging to a deceased individual must result in immediate rejection of the "
            "loan application. PAN format must match the regex: [A-Z]{5}[0-9]{4}[A-Z]{1}"
        ),
        spacer(),
        build_table(
            [
                ["Loan Amount Threshold", "PAN Mandatory?", "Aadhaar Mandatory?", "Form 60 Alternative?"],
                ["Up to Rs 50,000",       "No",             "No",                  "Yes"],
                ["Rs 50,001 to Rs 5 Lakhs","Yes",           "Recommended",         "No"],
                ["Above Rs 5 Lakhs",       "Yes",           "Yes (eKYC preferred)", "No"],
            ],
            col_widths=[5*cm, 4*cm, 5*cm, 4*cm]
        ),
        spacer(),
        heading2("3. Aadhaar-Based eKYC"),
        body(
            "Section 3.1 — eKYC Process: Banks may use Aadhaar-based eKYC for digital onboarding of "
            "loan applicants. Biometric authentication (fingerprint or iris scan) is the preferred mode. "
            "OTP-based eKYC is permitted for loan amounts up to Rs 60,000 per year per borrower. "
            "For loan amounts above Rs 60,000, full biometric eKYC or in-person verification (IPV) "
            "is mandatory."
        ),
        spacer(),
        heading2("4. Address Verification"),
        body(
            "Section 4.1 — Proof of Address: Acceptable documents for address verification include: "
            "(a) Aadhaar Card, (b) Voter ID, (c) Passport, (d) Driving Licence, (e) Recent utility "
            "bills (not older than 3 months), (f) Bank account statements (not older than 3 months). "
            "The address on the loan application must match the KYC address document. Any discrepancy "
            "must be escalated to the KYC compliance team."
        ),
        spacer(),
        heading2("5. Politically Exposed Persons (PEPs) and High-Risk Customers"),
        body(
            "Section 5.1 — Enhanced Due Diligence: Loan applications from Politically Exposed Persons "
            "(PEPs), their family members, or close associates must undergo Enhanced Due Diligence (EDD). "
            "EDD includes: (a) approval from senior management, (b) source of wealth verification, "
            "(c) enhanced transaction monitoring for the life of the loan, and (d) annual review."
        ),
        spacer(),
        heading2("6. KYC Compliance Violations"),
        body(
            "Section 6.1 — Penalty for Non-Compliance: Failure to complete KYC before loan disbursal "
            "constitutes a regulatory violation under PMLA 2002. Banks found in violation are subject "
            "to: (a) monetary penalty up to Rs 1 Crore per violation, (b) mandatory reporting to "
            "Financial Intelligence Unit India (FIU-IND), (c) potential suspension of loan operations "
            "in the affected branch. All KYC documents must be retained for 5 years after loan closure."
        ),
        spacer(),
        heading2("7. Periodic KYC Updates"),
        body(
            "Section 7.1 — Re-KYC Requirements: Banks must update KYC records periodically: "
            "(a) High-risk customers — every 2 years, "
            "(b) Medium-risk customers — every 8 years, "
            "(c) Low-risk customers — every 10 years. "
            "Failure to update KYC may result in restrictions on loan account operations."
        ),
    ]

    doc.build(story)
    print(f"Created: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# PDF 3 — RBI Priority Sector Lending
# ══════════════════════════════════════════════════════════════════════════════
def create_rbi_priority_sector():
    path = os.path.join(OUTPUT_DIR, "rbi_priority_sector_lending.pdf")
    doc  = SimpleDocTemplate(path, pagesize=A4)
    story = []

    story += [
        heading1("Reserve Bank of India"),
        heading1("Priority Sector Lending — Classification and Targets"),
        body("Master Directions on Priority Sector Lending | RBI/2024-25/PSL/002"),
        spacer(),
        heading2("1. Priority Sector Lending Overview"),
        body(
            "Priority Sector Lending (PSL) refers to loans and advances to certain sectors identified "
            "by the Reserve Bank of India as priority areas for the country's growth and development. "
            "All Scheduled Commercial Banks are required to achieve a PSL target of 40% of Adjusted "
            "Net Bank Credit (ANBC) or Credit Equivalent of Off-Balance Sheet Exposures (CEOBSE), "
            "whichever is higher."
        ),
        spacer(),
        heading2("2. Categories Classified as Priority Sector"),
        build_table(
            [
                ["Category",                "Sub-limit Target", "Key Eligibility Criteria"],
                ["Agriculture",              "18% of ANBC",      "Direct/indirect farming, agri-allied"],
                ["Micro Enterprises",        "7.5% of ANBC",     "Investment up to Rs 1 Cr in plant/machinery"],
                ["Small Enterprises",        "No sub-limit",     "Investment Rs 1-10 Cr"],
                ["Education Loans",          "No sub-limit",     "Studies in India; up to Rs 10 Lakhs"],
                ["Housing (Affordable)",     "No sub-limit",     "Loans up to Rs 35 Lakhs (metro); Rs 25 Lakhs (others)"],
                ["Renewable Energy",         "No sub-limit",     "Solar, wind, biogas projects"],
                ["Weaker Sections",          "12% of ANBC",      "SC/ST, minority communities, SHGs"],
                ["Social Infrastructure",   "No sub-limit",     "Schools, health, drinking water"],
            ],
            col_widths=[5*cm, 4*cm, 9*cm]
        ),
        spacer(),
        heading2("3. Housing Loans — Priority Sector Classification"),
        body(
            "Section 3.1 — Eligible Housing Loans: Housing loans extended by banks to individuals "
            "up to Rs 35 Lakhs in metropolitan centres (population above 10 Lakhs) and Rs 25 Lakhs in "
            "other centres qualify as Priority Sector loans, provided the overall cost of the dwelling "
            "unit does not exceed Rs 45 Lakhs and Rs 30 Lakhs respectively."
        ),
        spacer(),
        body(
            "Section 3.2 — Repair and Renovation Loans: Loans for repair of damaged dwelling units "
            "up to Rs 2 Lakhs in rural and semi-urban areas qualify for priority sector classification."
        ),
        spacer(),
        heading2("4. MSME Loans — Priority Sector Classification"),
        body(
            "Section 4.1 — Micro Enterprise: A manufacturing or services enterprise with investment "
            "in plant, machinery, or equipment not exceeding Rs 1 Crore AND turnover not exceeding "
            "Rs 5 Crores qualifies as a Micro Enterprise. All loans to such enterprises qualify for PSL."
        ),
        spacer(),
        body(
            "Section 4.2 — Small Enterprise: Investment above Rs 1 Crore but not exceeding Rs 10 Crores, "
            "with turnover not exceeding Rs 50 Crores, qualifies as a Small Enterprise."
        ),
        spacer(),
        heading2("5. Non-Achievement of PSL Targets"),
        body(
            "Section 5.1 — RIDF Contribution: Banks that fail to achieve PSL targets are required to "
            "deposit the shortfall amount in the Rural Infrastructure Development Fund (RIDF) maintained "
            "by NABARD, or other funds specified by RBI, at rates lower than market rates. This effectively "
            "penalises banks for non-achievement of PSL targets."
        ),
        spacer(),
        heading2("6. Reporting Requirements"),
        body(
            "Banks must submit quarterly PSL data to RBI in the format prescribed. Priority sector "
            "loans must be tagged in the Core Banking System (CBS) with appropriate PSL category codes. "
            "Mis-tagging of loans under priority sector is treated as a compliance violation."
        ),
    ]

    doc.build(story)
    print(f"Created: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# PDF 4 — Basel III Capital Framework
# ══════════════════════════════════════════════════════════════════════════════
def create_basel3_framework():
    path = os.path.join(OUTPUT_DIR, "basel3_capital_framework.pdf")
    doc  = SimpleDocTemplate(path, pagesize=A4)
    story = []

    story += [
        heading1("Basel III Capital and Risk Framework"),
        heading1("Summary for Indian Banks — RBI Implementation"),
        body("Reference: RBI Guidelines on Basel III Capital Regulations | DBOD.No.BP.BC.98/21.06.201/2011-12"),
        spacer(),
        heading2("1. Overview of Basel III in India"),
        body(
            "The Reserve Bank of India has implemented the Basel III Capital Regulations for Indian banks "
            "effective April 1, 2013, with full implementation by March 31, 2019. Basel III aims to "
            "strengthen the regulation, supervision, and risk management of banks. The framework sets "
            "minimum capital requirements, introduces capital buffers, and establishes leverage and "
            "liquidity standards."
        ),
        spacer(),
        heading2("2. Capital Adequacy Requirements"),
        build_table(
            [
                ["Capital Component",             "Minimum Ratio (Basel III)", "RBI Requirement"],
                ["Common Equity Tier 1 (CET1)",   "4.5%",                      "5.5%"],
                ["Additional Tier 1 (AT1)",       "1.5%",                      "1.5%"],
                ["Tier 1 Capital Total",          "6.0%",                      "7.0%"],
                ["Tier 2 Capital",                "2.0%",                      "2.0%"],
                ["Total Capital (CRAR)",          "8.0%",                      "9.0%"],
                ["Capital Conservation Buffer",   "2.5%",                      "2.5%"],
                ["Total with Buffer",             "10.5%",                     "11.5%"],
            ],
            col_widths=[8*cm, 5*cm, 5*cm]
        ),
        spacer(),
        heading2("3. Risk-Weighted Assets (RWA) for Loans"),
        body(
            "Section 3.1 — Retail Loan Risk Weights: Under the Standardised Approach, the following "
            "risk weights apply to retail loans for calculation of Risk-Weighted Assets:"
        ),
        spacer(),
        build_table(
            [
                ["Loan Category",              "Risk Weight",  "Notes"],
                ["Home Loans (LTV up to 75%)", "35%",          "Standard residential mortgage"],
                ["Home Loans (LTV 75-90%)",    "50%",          "Higher LTV = higher capital charge"],
                ["Home Loans (LTV above 90%)", "75-100%",      "Regulatory LTV breach; penalised"],
                ["Personal Loans (Unsecured)", "100-125%",     "Higher risk weight; no collateral"],
                ["Vehicle Loans",              "100%",         "Standard retail risk weight"],
                ["Business Loans (MSME)",      "75%",          "SME retail portfolio qualifier"],
                ["Business Loans (Large)",     "100%",         "Corporate exposure risk weight"],
                ["Non-Performing Loans (NPA)", "150%",         "Secured NPA; unsecured NPA = 150%"],
            ],
            col_widths=[7*cm, 4*cm, 7*cm]
        ),
        spacer(),
        heading2("4. Credit Risk Classification — Risk Tiers"),
        body(
            "Section 4.1 — Internal Rating System: Banks using the Internal Ratings-Based (IRB) "
            "approach must classify borrowers into risk tiers based on Probability of Default (PD), "
            "Loss Given Default (LGD), and Exposure at Default (EAD). The following guidelines apply "
            "to retail loan portfolios under the standardised approach:"
        ),
        spacer(),
        build_table(
            [
                ["Risk Tier",  "Bureau Score Range", "FOIR Range",   "Capital Charge Multiplier"],
                ["Low Risk",   "750 and above",      "Below 40%",    "1.0x base risk weight"],
                ["Medium Risk","650 - 749",          "40% - 55%",    "1.25x base risk weight"],
                ["High Risk",  "550 - 649",          "55% - 65%",    "1.5x base risk weight"],
                ["Very High",  "Below 550",          "Above 65%",    "2.0x base risk weight"],
            ],
            col_widths=[4*cm, 5*cm, 4*cm, 5*cm]
        ),
        spacer(),
        heading2("5. Leverage Ratio Requirements"),
        body(
            "Section 5.1: Banks must maintain a minimum Leverage Ratio of 4% (RBI requirement, "
            "higher than Basel III minimum of 3%). The leverage ratio is calculated as Tier 1 Capital "
            "divided by total on- and off-balance-sheet exposures. High-volume retail lending must "
            "be monitored to ensure leverage ratio compliance."
        ),
        spacer(),
        heading2("6. Liquidity Coverage Ratio (LCR)"),
        body(
            "Section 6.1 — LCR Standard: Banks must maintain a Liquidity Coverage Ratio of at least "
            "100%. This requires holding sufficient High-Quality Liquid Assets (HQLA) to cover net "
            "cash outflows over a 30-day stress period. Loan disbursals must be factored into LCR "
            "calculations on a daily basis."
        ),
        spacer(),
        heading2("7. Implications for Loan Underwriting"),
        body(
            "Under Basel III, the cost of capital for high-risk loans is significantly higher than "
            "for low-risk loans due to elevated risk weights. Banks should price loans accordingly, "
            "applying higher interest rates to high-risk borrowers to compensate for the additional "
            "capital required to be held against those exposures. Very high-risk loan applications "
            "where FOIR exceeds 65% or bureau score is below 550 must be declined or subject to "
            "mandatory senior credit committee approval with documentation of risk mitigation measures."
        ),
    ]

    doc.build(story)
    print(f"Created: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# PDF 5 — Internal Credit Policy (Mock Bank)
# ══════════════════════════════════════════════════════════════════════════════
def create_internal_credit_policy():
    path = os.path.join(OUTPUT_DIR, "internal_credit_policy.pdf")
    doc  = SimpleDocTemplate(path, pagesize=A4)
    story = []

    story += [
        heading1("IndiaFirst National Bank"),
        heading1("Internal Credit Policy — Retail Lending"),
        body("Policy Version: 4.2 | Effective: January 1, 2024 | Classification: Internal"),
        body("Approved by: Board Credit Committee | Review Date: December 31, 2024"),
        spacer(),
        heading2("1. Policy Objectives"),
        body(
            "This Internal Credit Policy (ICP) governs all retail lending decisions at IndiaFirst "
            "National Bank. It sets out eligibility criteria, financial benchmarks, documentation "
            "requirements, and approval authorities for loans extended to individual and MSME borrowers. "
            "This policy is supplementary to and consistent with all applicable RBI guidelines."
        ),
        spacer(),
        heading2("2. Eligibility Criteria"),
        build_table(
            [
                ["Parameter",              "Salaried",              "Self-Employed",         "Business Owner"],
                ["Minimum Age",            "21 years",              "25 years",              "25 years"],
                ["Maximum Age at Maturity","60 years",              "65 years",              "65 years"],
                ["Minimum Income",         "Rs 3 Lakhs p.a.",       "Rs 5 Lakhs p.a.",       "Rs 5 Lakhs p.a."],
                ["Min Employment Tenure",  "1 year current employer","3 years in business",  "5 years in business"],
                ["Min Bureau Score",       "650",                   "675",                   "675"],
            ],
            col_widths=[5*cm, 4.5*cm, 4.5*cm, 4.5*cm]
        ),
        spacer(),
        heading2("3. Product-Level Credit Parameters"),
        heading2("3.1 — Home Loan Policy"),
        build_table(
            [
                ["Parameter",         "Limit / Requirement"],
                ["Minimum Loan Amount","Rs 5 Lakhs"],
                ["Maximum Loan Amount","Rs 5 Crores (salaried); Rs 3 Crores (self-employed)"],
                ["Maximum Tenure",    "30 years (subject to retirement age)"],
                ["Maximum LTV",       "As per RBI norms (90% / 80% / 75% based on amount)"],
                ["Minimum Bureau Score","650"],
                ["Maximum FOIR",      "50% (salaried); 55% (self-employed)"],
                ["Collateral",        "Mortgage of the financed property (mandatory)"],
            ],
            col_widths=[6*cm, 12*cm]
        ),
        spacer(),
        heading2("3.2 — Personal Loan Policy"),
        build_table(
            [
                ["Parameter",         "Limit / Requirement"],
                ["Minimum Loan Amount","Rs 25,000"],
                ["Maximum Loan Amount","Rs 25 Lakhs (unsecured); Rs 50 Lakhs (with collateral)"],
                ["Maximum Tenure",    "7 years"],
                ["Minimum Bureau Score","700 (unsecured); 650 (secured)"],
                ["Maximum FOIR",      "50% (standard); up to 55% with senior officer approval"],
                ["Collateral",        "Not required; if provided, enhances approval probability"],
                ["Age at Loan Maturity","Maximum 60 years"],
            ],
            col_widths=[6*cm, 12*cm]
        ),
        spacer(),
        heading2("3.3 — Business Loan Policy"),
        build_table(
            [
                ["Parameter",         "Limit / Requirement"],
                ["Minimum Loan Amount","Rs 2 Lakhs"],
                ["Maximum Loan Amount","Rs 2 Crores (MSME); Rs 10 Crores (large enterprises)"],
                ["Maximum Tenure",    "15 years"],
                ["Minimum Bureau Score","675"],
                ["Maximum FOIR",      "55% (standard)"],
                ["Business Vintage",  "Minimum 3 years of operations"],
                ["Documentation",     "ITR for 2 years, GST returns for 12 months, bank statements for 6 months"],
            ],
            col_widths=[6*cm, 12*cm]
        ),
        spacer(),
        heading2("4. Mandatory Rejection Criteria (Hard Stops)"),
        body(
            "The following conditions shall result in AUTOMATIC REJECTION of the loan application "
            "without escalation to the credit committee:"
        ),
        spacer(),
        build_table(
            [
                ["Hard Stop Condition",                               "Applicable Loan Types"],
                ["Past loan default in any bank in last 5 years",     "All"],
                ["Bureau score below 550",                            "All"],
                ["FOIR above 65%",                                    "All"],
                ["PAN not provided for loans above Rs 50,000",        "All"],
                ["PAN invalid or inactive per IT database",           "All"],
                ["Unsecured personal loan above Rs 25 Lakhs without co-applicant","Personal"],
                ["LTV above 90% for home loans up to Rs 30 Lakhs",   "Home"],
                ["LTV above 80% for home loans Rs 30-75 Lakhs",      "Home"],
                ["LTV above 75% for home loans above Rs 75 Lakhs",   "Home"],
                ["Loan tenure exceeding maximum permitted",           "All"],
                ["Applicant on CIBIL defaulter list or RBI watchlist","All"],
            ],
            col_widths=[11*cm, 7*cm]
        ),
        spacer(),
        heading2("5. Escalation and Approval Authority"),
        build_table(
            [
                ["Loan Amount",           "Approval Authority"],
                ["Up to Rs 10 Lakhs",     "Branch Credit Officer"],
                ["Rs 10 Lakhs to Rs 50 Lakhs","Regional Credit Manager"],
                ["Rs 50 Lakhs to Rs 2 Crores","Zonal Credit Head"],
                ["Above Rs 2 Crores",     "Central Credit Committee"],
                ["Any hard stop override","Board Credit Committee (rare; documented)"],
            ],
            col_widths=[7*cm, 11*cm]
        ),
        spacer(),
        heading2("6. Priority Sector Loan Tagging"),
        body(
            "Section 6.1 — All loans qualifying for Priority Sector Lending (PSL) classification "
            "must be tagged in the CBS at the time of disbursal. Loan officers must verify PSL "
            "eligibility before recommending sanction. Incorrect tagging is a compliance violation "
            "subject to disciplinary action. Loans eligible for PSL classification include: "
            "(a) Home loans up to Rs 35 Lakhs in metros and Rs 25 Lakhs in non-metros, "
            "(b) MSME loans to micro and small enterprises, "
            "(c) Education loans for studies in India up to Rs 10 Lakhs, "
            "(d) Loans to weaker sections as defined by RBI."
        ),
        spacer(),
        heading2("7. Policy Exceptions"),
        body(
            "Exceptions to this policy may be granted only by the Zonal Credit Head or above, "
            "must be documented with explicit risk justification, and must be reported in the "
            "monthly exception register. The exception register is reviewed by the Board Risk "
            "Committee quarterly. Systemic exceptions (more than 5% of portfolio) trigger a "
            "mandatory policy review."
        ),
    ]

    doc.build(story)
    print(f"Created: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating mock regulatory PDFs...\n")
    create_rbi_master_circular()
    create_rbi_kyc_guidelines()
    create_rbi_priority_sector()
    create_basel3_framework()
    create_internal_credit_policy()
    print(f"\nAll 5 PDFs saved to: {OUTPUT_DIR}/")
    print("Next step: run  python rag/ingest.py  to build the Chroma vector store.")