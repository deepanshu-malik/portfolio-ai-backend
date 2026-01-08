# Parallel PDF Generation with asyncio

## Overview
Production pattern for generating multiple PDFs concurrently using asyncio's run_in_executor to parallelize CPU-bound PDF rendering while maintaining async compatibility.

## Problem Solved
PDF generation with WeasyPrint is CPU-bound and blocking. Generating 4 PDFs sequentially takes 4x the time. Using asyncio's executor pattern allows parallel generation while keeping the async event loop responsive.

## Implementation Pattern

### Parallel Generation with Executor
```python
import asyncio
import io
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

class PDFGenerator:
    def __init__(self, data, templates_path):
        self.data = data
        self.env = Environment(loader=FileSystemLoader(templates_path))
    
    def _generate_pdf(self, template_name: str) -> io.BytesIO:
        """Synchronous PDF generation (CPU-bound)"""
        pdf_buffer = io.BytesIO()
        template = self.env.get_template(template_name)
        rendered_html = template.render(self.data)
        HTML(string=rendered_html).write_pdf(target=pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer
    
    async def generate_all_pdfs(self) -> dict:
        """Generate multiple PDFs in parallel"""
        loop = asyncio.get_event_loop()
        
        # Create tasks for parallel execution
        tasks = [
            loop.run_in_executor(None, self._generate_pdf, "WelcomeLetter.html"),
            loop.run_in_executor(None, self._generate_pdf, "EmiSchedule.html"),
            loop.run_in_executor(None, self._generate_pdf, "TermsAndConditions.html"),
        ]
        
        # Wait for all PDFs to complete
        results = await asyncio.gather(*tasks)
        
        return {
            "welcome_letter": results[0],
            "emi_schedule": results[1],
            "terms": results[2],
        }
```

### Merging PDFs
```python
from pypdf import PdfWriter

async def generate_and_merge(self) -> io.BytesIO:
    """Generate PDFs in parallel and merge into single document"""
    pdfs = await self.generate_all_pdfs()
    
    merger = PdfWriter()
    merger.append(pdfs["welcome_letter"])
    merger.append(pdfs["emi_schedule"])
    merger.append(pdfs["terms"])
    
    merged_pdf = io.BytesIO()
    merger.write(merged_pdf)
    merged_pdf.seek(0)
    
    return merged_pdf
```

### Parallel S3 Upload
```python
async def upload_pdfs_parallel(self, pdfs: dict, case_id: str) -> dict:
    """Upload multiple PDFs to S3 in parallel"""
    upload_tasks = []
    
    for name, pdf_buffer in pdfs.items():
        pdf_buffer.seek(0)
        filename = f"{case_id}_{name}.pdf"
        upload_tasks.append(
            self.s3_service.upload(pdf_buffer, filename)
        )
    
    results = await asyncio.gather(*upload_tasks)
    
    return {
        name: result 
        for name, result in zip(pdfs.keys(), results)
    }
```

## Key Design Decisions

### Why run_in_executor?
- WeasyPrint is synchronous and CPU-bound
- Blocking the event loop would prevent concurrent request handling
- Executor runs blocking code in thread pool
- Event loop remains responsive for I/O operations

### Why asyncio.gather?
- Runs all tasks concurrently
- Waits for all to complete before continuing
- Returns results in same order as input tasks
- Exceptions can be handled with `return_exceptions=True`

### Thread Pool vs Process Pool
- Thread pool (default) works well for I/O-bound + moderate CPU
- Process pool better for heavy CPU (avoids GIL)
- For PDF generation, thread pool is sufficient

## Performance Impact
- Sequential: 4 PDFs × 2s each = 8 seconds
- Parallel: 4 PDFs concurrent = ~2.5 seconds
- **3x speedup** for document generation

## Production Considerations
- Set appropriate thread pool size for workload
- Handle individual PDF failures gracefully
- Clean up BytesIO buffers after use
- Monitor memory usage for large batches

## Error Handling
```python
async def generate_with_fallback(self) -> dict:
    """Generate PDFs with error handling"""
    loop = asyncio.get_event_loop()
    
    tasks = [
        loop.run_in_executor(None, self._generate_pdf, template)
        for template in self.templates
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    pdfs = {}
    for template, result in zip(self.templates, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to generate {template}: {result}")
            pdfs[template] = None
        else:
            pdfs[template] = result
    
    return pdfs
```

## GitHub Reference
Pattern implemented in Welcome Letter Automation Service for generating multi-language loan documents.
