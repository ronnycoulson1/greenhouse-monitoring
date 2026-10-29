import streamlit as st
from utils import sidebar

sidebar.render_sidebar()

st.html("""
<style>
@keyframes scrollUp {
    0%   { transform: translateY(100%); }
    100% { transform: translateY(-100%); }
}

.credits-container {
    height: 70vh;
    overflow: hidden;
    position: relative;
    background: #0a0a0a;
    border-radius: 12px;
    padding: 0 2rem;
}

.credits-scroll {
    animation: scrollUp 15s linear infinite;
    text-align: center;
    color: #e0e0e0;
    font-family: 'Georgia', serif;
}

.credits-scroll h1 { color: #a8d5a2; font-size: 2rem; margin-bottom: 0.25rem; }
.credits-scroll h2 { color: #c8e6c9; font-size: 1.2rem; margin: 2rem 0 0.5rem; border-bottom: 1px solid #333; padding-bottom: 0.5rem; }
.credits-scroll p  { color: #aaa; margin: 0.2rem 0; }
.credits-scroll .spacer { height: 80px; }
</style>

<div class="credits-container">
  <div class="credits-scroll">
    <div class="spacer"></div>
    <h1>🌿 Greenhouse Monitoring System</h1>
    <p><em>Grow smarter, not harder</em></p>

    <h2>Project Management</h2>
    <p>Caroline Shantery</p>

    <h2>Application Development</h2>
    <p>Yury Sergeev</p>
    <p>Ronny Coulson</p>
    <p>Paige Ogden</p>
    <p>Henry Zheng</p>
    <p>Mololuwa Foluso</p>
    <p>Md Ijtihad Chowdhury</p>
    <p> Festo Mwakondo</p>
    <p>Rylan Bowe</p>
    <p>Contributor Name</p>

    <h2>Special Thanks</h2>
    <p>Melissa Davis</p>

    <h2>Built With</h2>
    <h3>Frontend</h3>
    <p>Streamlit<p>
    <p>HTML/CSS</p>
    <p>Javascript</p>
    <h3>Backend</h3>
    <p>MongoDB</p>
    <p>Flask</p>
    <h3>Hardware</h3>
    <p>Raspberry Pi Pico W</p>
    <p>DHT11 Sensors</p>

    <div class="spacer"></div>
    <p><em>Version 1.0.0</em></p>
    <div class="spacer"></div>
  </div>
</div>
""")