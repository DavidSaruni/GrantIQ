from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime

from grants.models import Grant, GrantDocument


def _esc(text):
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


def _wrap(text, width=88):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if len(trial) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def build_pdf(title, paragraphs):
    ops = []
    y = 750
    ops.append(f"BT /F1 16 Tf 50 {y} Td ({_esc(title[:70])}) Tj ET")
    y -= 30
    for para in paragraphs:
        for line in _wrap(para):
            if y < 60:
                break
            ops.append(f"BT /F1 11 Tf 50 {y} Td ({_esc(line)}) Tj ET")
            y -= 15
        y -= 8
        if y < 60:
            break
    stream = "\n".join(ops).encode("latin-1")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    )
    objects.append(
        b"4 0 obj << /Length "
        + str(len(stream)).encode("ascii")
        + b" >> stream\n"
        + stream
        + b"\nendstream endobj\n"
    )
    objects.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")

    header = b"%PDF-1.4\n"
    body = b"".join(objects)
    offsets = []
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        cursor += len(obj)
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode("ascii")
    xref_start = len(header) + len(body)
    trailer = (
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_start).encode("ascii")
        + b"\n%%EOF\n"
    )
    return header + body + xref + trailer


def aware(year, month, day, hour=9):
    return timezone.make_aware(datetime(year, month, day, hour, 0))


NRF_GRANTS = [
    {
        "title": "Collaborative Network for Vaccine Research in West and East Africa",
        "company": "National Research Fund (NRF Kenya)",
        "location": "East Africa",
        "grant_date": aware(2026, 8, 18),
        "deadline": aware(2026, 11, 30, 17),
        "description": """
<p>The National Research Fund of Kenya (NRF-Kenya), in partnership with the Uganda National Council for Science and Technology (UNCST) and counterparts in Tanzania, invites proposals to establish a collaborative network for vaccine research across West and East Africa.</p>
<h2>About this call</h2>
<p>This regional call supports joint research that strengthens vaccine discovery, development, manufacturing readiness, and public-health response capacity. Consortia should demonstrate complementary expertise across participating countries and a clear pathway from research to impact.</p>
<h3>Priority areas</h3>
<ul>
  <li>Vaccine discovery and candidate development for diseases of regional importance</li>
  <li>Clinical and immunological research, including trial readiness</li>
  <li>Local manufacturing, cold-chain, and delivery systems</li>
  <li>Community engagement, ethics, and regulatory science</li>
</ul>
<h3>Who can apply</h3>
<p>Eligible lead applicants are public universities, research institutes, and legally registered research organisations in Kenya, Uganda, or Tanzania, working with partners in West and/or East Africa.</p>
<p>For more information please download document below:</p>
""",
        "pdf_paragraphs": [
            "CALL FOR PROPOSALS",
            "Collaborative Network for Vaccine Research in West and East Africa",
            "Issued by the National Research Fund of Kenya (NRF-Kenya) in partnership with the Uganda National Council for Science and Technology (UNCST) and Tanzanian counterparts.",
            "This document summarises the call objectives, eligibility, and submission requirements for testing the GrantIQ document viewer.",
            "Applicants should form multidisciplinary consortia, describe work packages, budgets, and data-sharing plans, and demonstrate how the network will build sustainable vaccine research capacity in the region.",
        ],
    },
    {
        "title": "SGCI STISA 2034 Multi-Country Research Call",
        "company": "Science Granting Councils Initiative (SGCI)",
        "location": "Africa",
        "grant_date": aware(2026, 7, 6),
        "deadline": aware(2026, 10, 15, 17),
        "description": """
<p>Calling African researchers. The Science Granting Councils Initiative (SGCI) has launched a competitive multilateral research call to advance Africa’s Science, Technology and Innovation priorities under STISA 2034.</p>
<h2>Why this call</h2>
<p>The call funds multi-country teams whose work contributes to continental STI goals, including industrialisation, public health, food systems, climate resilience, and digital transformation.</p>
<h3>Requirements</h3>
<ol>
  <li>Projects must involve researchers from at least two African countries.</li>
  <li>Proposals should show policy relevance and pathways to use of results.</li>
  <li>Early-career researchers and women scientists are strongly encouraged as co-investigators.</li>
</ol>
<p>Full guidelines, budget templates, and the online submission process are in the attached call document.</p>
""",
        "pdf_paragraphs": [
            "SGCI STISA 2034 Multi-Country Research Call",
            "The Science Granting Councils Initiative has launched a competitive multilateral research call to advance Africa's Science, Technology and Innovation priorities.",
            "Eligible teams must include investigators from at least two African countries and align proposed work with STISA 2034 pillars.",
            "This sample PDF is provided so GrantIQ can demonstrate in-page viewing and download of attached call documents.",
        ],
    },
    {
        "title": "Call for Applications for Researchers and Science-based Entrepreneurs",
        "company": "Swiss Leading House for Africa",
        "location": "International",
        "grant_date": aware(2026, 6, 12),
        "deadline": aware(2026, 9, 30, 17),
        "description": """
<p>We are delighted to announce two open opportunities from the Swiss Leading House for Africa. Researchers across disciplines are encouraged to apply, together with science-based entrepreneurs seeking to translate research into products and services.</p>
<h2>Two tracks</h2>
<ul>
  <li><strong>Researchers:</strong> mobility, joint projects, and partnership development with Swiss institutions.</li>
  <li><strong>Science-based entrepreneurs:</strong> support for validation, prototyping, and market-oriented research.</li>
</ul>
<h3>Eligibility</h3>
<p>Applicants should be based at an African university, research organisation, or recognised innovation hub, and propose collaboration with a Swiss partner.</p>
<p>Please review the attached information pack for track-specific criteria, eligible costs, and the application checklist.</p>
""",
        "pdf_paragraphs": [
            "Swiss Leading House for Africa",
            "Call for Applications for Researchers and Science-based Entrepreneurs",
            "Two open opportunities are available: a researcher track for joint projects and mobility, and an entrepreneurship track for science-based ventures.",
            "Download and complete this information pack alongside your online application. This file is a sample attachment for GrantIQ testing.",
        ],
    },
    {
        "title": "EDCTP Forum 2027",
        "company": "EDCTP",
        "location": "International",
        "grant_date": aware(2026, 6, 12),
        "deadline": aware(2026, 12, 15, 17),
        "description": """
<p>EDCTP call for abstracts, scientific symposium, workshops and applications for EDCTP prizes. The EDCTP Forum 2027 will bring together researchers, funders, and policymakers working on clinical trials and poverty-related infectious diseases.</p>
<h2>What you can submit</h2>
<ul>
  <li>Scientific abstracts (oral and poster)</li>
  <li>Scientific symposium proposals</li>
  <li>Workshop concepts</li>
  <li>Applications for EDCTP prizes</li>
</ul>
<p>Successful submissions will be programmed as part of the Forum. Please consult the attached call text for themes, word limits, and review criteria.</p>
""",
        "pdf_paragraphs": [
            "EDCTP Forum 2027 - Call for abstracts, symposia, workshops and prizes",
            "The EDCTP Forum 2027 invites the global health research community to submit abstracts, scientific symposium proposals, workshops, and prize nominations.",
            "This sample document stands in for the official call pack so that the grant detail page can embed a PDF with a download option.",
        ],
    },
    {
        "title": "Royal Society Funding Opportunities",
        "company": "The Royal Society",
        "location": "International",
        "grant_date": aware(2026, 5, 29),
        "deadline": aware(2026, 10, 31, 17),
        "description": """
<p>Royal Society Wolfson Fellowship and Wolfson Visiting Fellowship. These schemes offer established or emerging international scientific research leaders the opportunity to work with UK host institutions, strengthening research capacity and collaboration.</p>
<h2>Schemes</h2>
<h3>Wolfson Fellowship</h3>
<p>Supports outstanding international researchers who wish to undertake a long-term relocation to a UK university or research institution.</p>
<h3>Wolfson Visiting Fellowship</h3>
<p>Supports shorter research visits by international scientific leaders, enabling knowledge exchange and new collaborations.</p>
<p>Eligibility, duration, and eligible costs differ by scheme. Download the guidance notes below before starting an application.</p>
""",
        "pdf_paragraphs": [
            "Royal Society Wolfson Fellowship and Wolfson Visiting Fellowship",
            "These schemes offer established or emerging international scientific research leaders the opportunity to work with UK host organisations.",
            "This sample guidance note is attached for GrantIQ so users can preview the PDF in the page and download a copy.",
        ],
    },
]


class Command(BaseCommand):
    help = "Load five example grants and calls from nrf.go.ke for local testing."

    def handle(self, *args, **options):
        User = get_user_model()
        creator = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if creator is None:
            self.stderr.write("Create a user before seeding grants.")
            return

        created = 0
        for item in NRF_GRANTS:
            grant, was_created = Grant.objects.get_or_create(
                title=item["title"],
                defaults={
                    "creator": creator,
                    "company": item["company"],
                    "location": item["location"],
                    "description": item["description"].strip(),
                    "grant_date": item["grant_date"],
                    "deadline": item["deadline"],
                    "is_published": True,
                    "role": "Research",
                    "contract": "Organization",
                    "about": item["company"],
                    "salary": 0,
                    "experience": "",
                    "vacancy": "",
                },
            )
            if was_created:
                created += 1
            else:
                grant.description = item["description"].strip()
                grant.company = item["company"]
                grant.location = item["location"]
                grant.grant_date = item["grant_date"]
                grant.deadline = item["deadline"]
                grant.is_published = True
                grant.save()

            if not grant.documents.exists():
                pdf_bytes = build_pdf(item["title"], item["pdf_paragraphs"])
                filename = f"{grant.slug or 'grant'}-call-document.pdf"
                doc = GrantDocument(grant=grant, title=f"{item['title']} — Call document")
                doc.file.save(filename, ContentFile(pdf_bytes), save=True)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded NRF grants and calls. New records: {created}. Total examples: {len(NRF_GRANTS)}."
        ))
