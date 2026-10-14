
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from app.models import PayslipRequest
from app.pdf_service import generate_payslip_pdf

app = FastAPI(
    title="Payslip Generator API",
    description="Generate employee payslips as PDF files",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post(
    "/api/payslips/generate",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Generated payslip PDF",
            "content": {
                "application/pdf": {}
            },
        }
    },
)
def generate_payslip(request: PayslipRequest):
    pdf_buffer = generate_payslip_pdf(request)

    employee_name = "".join(
        char if char.isalnum() else "_"
        for char in request.employee.employee_name
    ).strip("_") or "Employee"

    filename = (
        f"Payslip_{employee_name}_"
        f"{request.year}_{request.month:02d}.pdf"
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )





    
