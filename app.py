import streamlit as st
import pytesseract
from PIL import Image
import io
import fitz  # PyMuPDF for reading PDFs and converting to images
from pypdf import PdfWriter, PdfReader  # For merging OCR'd PDF pages

# --- Page Configuration ---
st.set_page_config(page_title="Voter List to Searchable PDF", page_icon="📄", layout="centered")

st.title("📄 Image/PDF to Searchable PDF")
st.markdown("""
Upload a **Voter List** (Image or PDF format). This app uses advanced OCR (Optical Character Recognition) 
to read the text and create a new PDF. 

✨ **The original visual format is perfectly preserved**, but all the text becomes **searchable (Ctrl+F) and copyable**.
""")

st.divider()

# --- File Uploader ---
# Now accepts both PDFs and standard image formats
uploaded_file = st.file_uploader(
    "📁 Select Voter List from PC (PDF, JPG, PNG)", 
    type=["pdf", "jpg", "jpeg", "png"],
    help="Upload your scanned document here."
)

if uploaded_file is not None:
    # Determine the file type
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    # --- Preview Section ---
    st.subheader("Preview")
    if file_extension in ['jpg', 'jpeg', 'png']:
        image = Image.open(uploaded_file)
        st.image(image, caption=f'Preview: {uploaded_file.name}', use_container_width=True)
    elif file_extension == 'pdf':
        st.info(f"📄 PDF Document Uploaded: **{uploaded_file.name}**. Ready for processing.")

    st.divider()

    # --- Process Button ---
    # Prominent start button placed after the upload and preview
    if st.button('🚀 Start OCR Conversion', type="primary", use_container_width=True):
        
        with st.spinner('Running OCR Engine... This might take a moment depending on file size.'):
            try:
                pdf_writer = PdfWriter()
                
                # --- LOGIC 1: If an Image was uploaded ---
                if file_extension in ['jpg', 'jpeg', 'png']:
                    # Re-open image from uploaded file just to be safe
                    uploaded_file.seek(0)
                    image = Image.open(uploaded_file)
                    
                    # Create an invisible text layer over the original image
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
                    
                    # Read the resulting PDF bytes and add to our writer
                    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
                    pdf_writer.add_page(pdf_reader.pages[0])
                    
                # --- LOGIC 2: If a PDF was uploaded ---
                elif file_extension == 'pdf':
                    uploaded_file.seek(0)
                    # Open PDF using PyMuPDF (fitz)
                    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    total_pages = len(pdf_document)
                    
                    # Show a progress bar for multi-page PDFs
                    progress_text = "Processing Pages..."
                    progress_bar = st.progress(0, text=progress_text)
                    
                    for page_num in range(total_pages):
                        # Extract page as a high-resolution image (300 DPI is best for OCR)
                        page = pdf_document.load_page(page_num)
                        pix = page.get_pixmap(dpi=300)
                        img_data = pix.tobytes("png")
                        image = Image.open(io.BytesIO(img_data))
                        
                        # Run OCR on this specific page
                        page_pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
                        
                        # Append the processed page to our final PDF
                        pdf_reader = PdfReader(io.BytesIO(page_pdf_bytes))
                        pdf_writer.add_page(pdf_reader.pages[0])
                        
                        # Update progress bar
                        progress_bar.progress((page_num + 1) / total_pages, text=f"Processed page {page_num + 1} of {total_pages}")
                
                # --- Save and Output ---
                final_pdf_bytes = io.BytesIO()
                pdf_writer.write(final_pdf_bytes)
                final_pdf_bytes.seek(0)

                st.success("✅ Conversion complete! Your document is now fully searchable.")

                # --- Download Button ---
                base_name = uploaded_file.name.rsplit('.', 1)[0]
                st.download_button(
                    label="⬇️ Download Searchable PDF",
                    data=final_pdf_bytes,
                    file_name=f"searchable_{base_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except pytesseract.TesseractNotFoundError:
                st.error("❌ Tesseract OCR is not installed or not in your system PATH. Ensure 'packages.txt' has 'tesseract-ocr' if deploying on Streamlit Cloud.")
            except Exception as e:
                st.error(f"❌ An error occurred during conversion: {e}")

st.markdown("---")
st.caption("Note: Accuracy depends on original image quality. Watermarks like 'UNDER ADJUDICATION' might overlap with text slightly in the OCR output, but visual format will remain 100% identical.")
