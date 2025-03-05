import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageColor
import numpy as np

def create_gradient(size, color1, color2, mode="linear"):
    width, height = size
    
    if mode == "linear":
        gradient = np.linspace(0, 1, width)
        gradient = np.tile(gradient, (height, 1))
    elif mode == "radial":
        x, y = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))
        gradient = np.sqrt(x**2 + y**2)
        gradient = gradient / gradient.max()
    
    r1, g1, b1 = ImageColor.getrgb(color1)
    r2, g2, b2 = ImageColor.getrgb(color2)
    gradient_r = (1 - gradient) * r1 + gradient * r2
    gradient_g = (1 - gradient) * g1 + gradient * g2
    gradient_b = (1 - gradient) * b1 + gradient * b2
    
    gradient_image = np.stack([gradient_r, gradient_g, gradient_b], axis=2).astype("uint8")
    return Image.fromarray(gradient_image)

def generate_qr_code_with_gradient(data, color1, color2, gradient_mode, image_path=None, size=10, quality=300, text="", text_color="black", text_size=100, font_name="arial.ttf", logo_size_ratio=0.40, transparency=255):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    max_size = 2000
    final_size = min(size * quality, max_size)
    img = img.resize((final_size, final_size), Image.LANCZOS)
    
    gradient = create_gradient(img.size, color1, color2, mode=gradient_mode)
    
    colored_img = Image.new("RGB", img.size)
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            if img.getpixel((x, y)) != (255, 255, 255):
                r, g, b = gradient.getpixel((x, y))
                colored_img.putpixel((x, y), (int(r), int(g), int(b)))
            else:
                colored_img.putpixel((x, y), (255, 255, 255))
    
    if image_path:
        logo = Image.open(image_path).convert("RGBA")
        alpha = logo.getchannel("A")
        alpha = alpha.point(lambda p: p * (transparency / 255))
        logo.putalpha(alpha)
        logo_size = int(min(img.size) * logo_size_ratio)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        pos = ((colored_img.size[0] - logo_size) // 2, (colored_img.size[1] - logo_size) // 2)
        colored_img.paste(logo, pos, mask=logo)
    
    if text:
        draw = ImageDraw.Draw(colored_img)
        try:
            font = ImageFont.truetype(font_name, text_size)
        except IOError:
            font = ImageFont.load_default()
        text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
        text_position = ((colored_img.size[0] - text_width) // 2, colored_img.size[1] - text_height - 50)
        draw.text(text_position, text, fill=text_color, font=font)
    
    return colored_img

def header_func(logo_url):
    cols1, cols2 = st.columns([1, 9], vertical_alignment= 'center', gap='small')  # This creates a 10% and 90% split
    with cols1:
        st.image(logo_url, width=300)
    with cols2:
        # Align title to the left
        title_html = """
        <div style="display: flex; align-items: center;">
            <h1 style='font-size: 60px;'>
                <span style='color: #6CB4EE;'>Amazon LCY3</span> 
                <span style='color: #1D2951;'>QR Code Generator</span>
            </h1>
        </div>
        """
        st.markdown(title_html, unsafe_allow_html=True)
logo_url = "Images/LCY3 Logo.png"
st.set_page_config(page_title='QR Code Generator for LCY3', page_icon=logo_url, layout="wide")
header_func(logo_url=logo_url)

col1, col2 = st.columns([4, 6])
st.sidebar.header("Settings")

color1 = st.sidebar.color_picker("Pick the start color for the gradient:", "#000000")
color2 = st.sidebar.color_picker("Pick the end color for the gradient:", "#FF0000")
gradient_mode = st.sidebar.selectbox("Select the gradient mode:", ["linear", "radial"])
text_color = st.sidebar.color_picker("Pick a color for the text:", "#000000")
size = st.sidebar.slider("Size of the QR Code:", 1, 20, 15)
quality = st.sidebar.slider("Quality (DPI):", 100, 900, 300)
text_size = st.sidebar.slider("Text Size:", 10, 500, 100)
font_name = st.sidebar.selectbox("Select Font:", ["arial.ttf", "times.ttf", "comic.ttf"])
logo_size_ratio = st.sidebar.slider("Logo Size Ratio (as % of QR size):", 0.1, 0.5, 0.5)
transparency = st.sidebar.slider("Logo Transparency (0-255):", 0, 255, 255)
file_format = st.sidebar.radio("Save as:", ["PNG", "JPEG"])

with col1:
    data = st.text_input("Enter data for QR Code:")
    image_path = st.file_uploader("Upload an image for the center (optional):", type=["png", "jpg", "jpeg"])
    text = st.text_input("Add text below the QR Code (optional):")

with col2:
    placeholder = st.empty()  # Create a placeholder for the QR code or loading message
    generate_qr = st.button("Generate QR Code")  # Add a button to trigger QR generation

    if generate_qr and data:  # Only generate when button is clicked
        placeholder.text("Please wait... Generating QR code...")  # Show loading message

        qr_image = generate_qr_code_with_gradient(
            data, color1, color2, gradient_mode, image_path, size, quality, text, text_color, text_size, font_name, logo_size_ratio, transparency
        )

        placeholder.image(qr_image, width=400)  # Replace the message with the QR code
        
        buffer = BytesIO()
        qr_image.save(buffer, format=file_format)
        buffer.seek(0)
        file_name = f"{data.replace(' ', '_')}.{file_format.lower()}"

        st.download_button(
            label="Download QR Code",
            data=buffer,
            file_name=file_name,
            mime=f"image/{file_format.lower()}"
        )
    elif generate_qr and not data:
        st.warning("Please enter data to generate your QR Code.")
