# streamlit_app.py - Updated with SteamDB-specific cookie handling and real traffic patterns
import streamlit as st
import sys
import os
import time
import json
import random
import uuid
import base64
import re  # ADDED for release date pattern matching

# Add the current directory to Python path to import the scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set page config
st.set_page_config(
    page_title="SteamDB & PSN Matcher",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with holographic design
st.markdown(""" 
<style> 
/* ============= MAIN HEADER ============= */
.main-header { 
    font-size: 3rem; 
    font-weight: bold; 
    text-align: center; 
    margin-bottom: 2rem; 
    background: linear-gradient(90deg, #0ff, #0070cc, #0ff); 
    -webkit-background-clip: text; 
    -webkit-text-fill-color: transparent; 
    text-shadow: 0 0 10px rgba(0, 255, 255, 0.3); 
    animation: header-glow 3s ease-in-out infinite alternate;
} 

@keyframes header-glow {
    0% { text-shadow: 0 0 10px rgba(0, 255, 255, 0.3), 0 0 20px rgba(0, 255, 255, 0.2); }
    100% { text-shadow: 0 0 20px rgba(0, 255, 255, 0.5), 0 0 40px rgba(0, 255, 255, 0.3), 0 0 60px rgba(0, 255, 255, 0.1); }
}

/* ============= HOLOGRAPHIC CARDS ============= */
.holographic-card { 
    background: rgba(17, 17, 17, 0.95) !important; 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
    border-radius: 15px !important; 
    padding: 1.5rem !important; 
    margin-bottom: 1rem !important; 
    position: relative !important; 
    overflow: hidden !important; 
    transition: all 0.5s ease !important; 
    backdrop-filter: blur(10px) !important; 
} 

.holographic-card::before { 
    content: '' !important; 
    position: absolute !important; 
    top: -50% !important; 
    left: -50% !important; 
    width: 200% !important; 
    height: 200% !important; 
    background: linear-gradient( 
        0deg,  
        transparent,  
        transparent 30%,  
        rgba(0,255,255,0.2) 
    ) !important; 
    transform: rotate(-45deg) !important; 
    transition: all 0.8s ease !important; 
    opacity: 0 !important; 
    z-index: 1 !important; 
} 

.holographic-card:hover::before { 
    opacity: 1 !important; 
    transform: rotate(-45deg) translateY(100%) !important; 
} 

.holographic-card:hover { 
    transform: translateY(-5px) scale(1.02) !important; 
    box-shadow:  
        0 0 30px rgba(0, 255, 255, 0.6), 
        0 0 60px rgba(0, 255, 255, 0.3), 
        inset 0 0 20px rgba(0, 255, 255, 0.1) !important; 
    border-color: rgba(0, 255, 255, 0.6) !important; 
} 

.holographic-text { 
    color: #0ff !important; 
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.5) !important; 
    position: relative !important; 
    z-index: 2 !important; 
} 

.holographic-subtext { 
    color: #8af !important; 
    text-shadow: 0 0 3px rgba(138, 255, 255, 0.3) !important; 
    position: relative !important; 
    z-index: 2 !important; 
} 

/* ============= EXPANDERS ============= */
div[data-testid="stExpander"] { 
    background: transparent !important; 
    border: none !important; 
    margin-bottom: 1.5rem !important; 
} 

div[data-testid="stExpander"] > div:first-child { 
    background: rgba(17, 17, 17, 0.95) !important; 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
    border-radius: 15px 15px 0 0 !important; 
    padding: 1rem 1.5rem !important; 
    transition: all 0.5s ease !important; 
} 

div[data-testid="stExpander"] > div:first-child:hover { 
    background: rgba(25, 25, 25, 0.95) !important; 
    border-color: rgba(0, 255, 255, 0.6) !important; 
    box-shadow: 0 0 20px rgba(0, 255, 255, 0.4) !important; 
} 

div[data-testid="stExpander"] div[role="button"] p { 
    color: #0ff !important; 
    font-weight: 600 !important; 
    margin: 0 !important; 
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.5) !important; 
} 

div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] { 
    background: rgba(17, 17, 17, 0.95) !important; 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
    border-top: none !important; 
    border-radius: 0 0 15px 15px !important; 
    padding: 1.5rem !important; 
    position: relative !important; 
    overflow: hidden !important; 
} 

div[data-testid="stExpander"] div[data-testid="stExpanderDetails"]::before { 
    content: '' !important; 
    position: absolute !important; 
    top: -50% !important; 
    left: -50% !important; 
    width: 200% !important; 
    height: 200% !important; 
    background: linear-gradient( 
        0deg,  
        transparent,  
        transparent 30%,  
        rgba(0,255,255,0.15) 
    ) !important; 
    transform: rotate(-45deg) !important; 
    transition: all 0.8s ease !important; 
    opacity: 0 !important; 
    z-index: 1 !important; 
} 

div[data-testid="stExpander"]:hover div[data-testid="stExpanderDetails"]::before { 
    opacity: 1 !important; 
    transform: rotate(-45deg) translateY(100%) !important; 
} 

div[data-testid="stExpander"] .stMarkdown p, 
div[data-testid="stExpander"] .stMarkdown strong, 
div[data-testid="stExpander"] .stMarkdown { 
    color: #0ff !important; 
    position: relative !important; 
    z-index: 2 !important; 
} 

div[data-testid="stExpander"] .stMarkdown a { 
    color: #8af !important; 
    text-decoration: none !important; 
    border-bottom: 1px solid rgba(138, 255, 255, 0.3) !important; 
    transition: all 0.3s ease !important; 
} 

div[data-testid="stExpander"] .stMarkdown a:hover { 
    color: #0ff !important; 
    border-bottom-color: #0ff !important; 
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.5) !important; 
} 

/* ============= TABS ============= */
.stTabs [data-baseweb="tab-list"] { 
    gap: 2px !important; 
    background: rgba(17, 17, 17, 0.9) !important; 
    border-radius: 10px !important; 
    padding: 0.5rem !important; 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
} 

.stTabs [data-baseweb="tab"] { 
    background: transparent !important; 
    border-radius: 8px !important; 
    padding: 10px 20px !important; 
    border: none !important; 
    color: #8af !important; 
    transition: all 0.3s ease !important; 
} 

.stTabs [aria-selected="true"] { 
    background: rgba(0, 255, 255, 0.2) !important; 
    color: #0ff !important; 
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.5) !important; 
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.3) !important; 
} 

.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) { 
    background: rgba(0, 255, 255, 0.1) !important; 
    color: #0ff !important; 
} 

/* ============= METRICS ============= */
.stMetric { 
    background: rgba(17, 17, 17, 0.95) !important; 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
    border-radius: 15px !important; 
    padding: 1.5rem !important; 
    transition: all 0.5s ease !important; 
    position: relative !important; 
    overflow: hidden !important; 
} 

.stMetric::before { 
    content: '' !important; 
    position: absolute !important; 
    top: -50% !important; 
    left: -50% !important; 
    width: 200% !important; 
    height: 200% !important; 
    background: linear-gradient( 
        0deg,  
        transparent,  
        transparent 30%,  
        rgba(0,255,255,0.1) 
    ) !important; 
    transform: rotate(-45deg) !important; 
    transition: all 0.8s ease !important; 
    opacity: 0 !important; 
    z-index: 1 !important; 
} 

.stMetric:hover::before { 
    opacity: 1 !important; 
    transform: rotate(-45deg) translateY(100%) !important; 
} 

.stMetric:hover { 
    transform: translateY(-3px) !important; 
    box-shadow: 0 0 25px rgba(0, 255, 255, 0.4) !important; 
    border-color: rgba(0, 255, 255, 0.6) !important; 
} 

[data-testid="stMetricValue"] { 
    color: #0ff !important; 
    font-weight: 700 !important; 
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.5) !important; 
    position: relative !important; 
    z-index: 2 !important; 
} 

[data-testid="stMetricLabel"] { 
    color: #8af !important; 
    position: relative !important; 
    z-index: 2 !important; 
} 

/* ============= SIZE CONSTRAINTS ============= */
.holographic-card,
.holographic-container,
div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    max-width: 100% !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

/* Prevent divs from exceeding viewport */
.main .block-container {
    max-width: 100vw !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* Responsive text sizing */
@media (max-width: 768px) {
    .main-header {
        font-size: 2rem !important;
    }
    
    .holographic-card,
    .holographic-container {
        padding: 1rem !important;
    }
}

/* ============= BUTTONS ============= */
.stButton button { 
    background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 112, 204, 0.2)) !important; 
    border: 1px solid rgba(0, 255, 255, 0.4) !important; 
    color: #0ff !important; 
    border-radius: 10px !important; 
    padding: 0.5rem 1.5rem !important; 
    transition: all 0.3s ease !important; 
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.5) !important; 
} 

.stButton button:hover { 
    background: linear-gradient(135deg, rgba(0, 255, 255, 0.3), rgba(0, 112, 204, 0.3)) !important; 
    border-color: #0ff !important; 
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.4) !important; 
    transform: translateY(-2px) !important; 
} 

.stButton button[kind="primary"] { 
    background: linear-gradient(135deg, #0070cc, #0ff) !important; 
    border: none !important; 
    color: #111 !important; 
    font-weight: bold !important; 
    text-shadow: none !important; 
} 

.stButton button[kind="primary"]:hover { 
    background: linear-gradient(135deg, #0ff, #0070cc) !important; 
    box-shadow: 0 0 20px rgba(0, 255, 255, 0.6) !important; 
} 

/* ============= DATAFRAMES ============= */
[data-testid="stDataFrame"] { 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
    border-radius: 15px !important; 
    background: rgba(17, 17, 17, 0.95) !important; 
    overflow: hidden !important; 
} 

/* ============= ALERTS ============= */
[data-testid="stAlert"] { 
    background: rgba(17, 17, 17, 0.95) !important; 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
    border-radius: 15px !important; 
    color: #0ff !important; 
    backdrop-filter: blur(10px) !important; 
} 

[data-testid="stProgress"] > div > div > div { 
    background: linear-gradient(90deg, #0ff, #0070cc) !important; 
} 

/* ============= TEXT INPUT ============= */
[data-testid="stTextInput"] input { 
    background: rgba(17, 17, 17, 0.95) !important; 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
    border-radius: 10px !important; 
    padding: 0.75rem 1rem !important; 
    color: #0ff !important; 
    transition: all 0.3s ease !important; 
} 

[data-testid="stTextInput"] input:focus { 
    border-color: #0ff !important; 
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.4) !important; 
    outline: none !important; 
} 

/* ============= TEXT AREA ============= */
[data-testid="stTextArea"] textarea { 
    background: rgba(17, 17, 17, 0.95) !important; 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
    border-radius: 10px !important; 
    padding: 0.75rem 1rem !important; 
    color: #0ff !important; 
    transition: all 0.3s ease !important; 
    font-family: monospace !important; 
} 

[data-testid="stTextArea"] textarea:focus { 
    border-color: #0ff !important; 
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.4) !important; 
    outline: none !important; 
} 

/* ============= GLOBAL STYLES ============= */
.stApp { 
    background: linear-gradient(135deg, #0a0a0a, #1a1a2e) !important; 
    color: #0ff !important; 
} 

.main .block-container { 
    color: #0ff !important; 
} 

.stMarkdown, .stText, .stCode { 
    color: #0ff !important; 
} 

/* ============= SIDEBAR ============= */
[data-testid="stSidebar"] { 
    background: rgba(10, 10, 10, 0.9) !important; 
    border-right: 1px solid rgba(0, 255, 255, 0.2) !important; 
} 

/* ============= FORM ELEMENTS ============= */
[data-testid="stRadio"] label { 
    color: #8af !important; 
} 

[data-testid="stSlider"] label { 
    color: #8af !important; 
} 

[data-testid="stSlider"] div[data-baseweb="slider"] { 
    background: rgba(0, 255, 255, 0.1) !important; 
} 

[data-testid="stCheckbox"] label { 
    color: #8af !important; 
} 

[data-testid="stMultiSelect"] label { 
    color: #8af !important; 
} 

[data-testid="stMultiSelect"] div[data-baseweb="select"] { 
    background: rgba(17, 17, 17, 0.95) !important; 
    border: 1px solid rgba(0, 255, 255, 0.3) !important; 
    color: #0ff !important; 
} 

/* ============= CAPTION ============= */
.stCaption { 
    color: #8af !important; 
    text-shadow: 0 0 3px rgba(0, 255, 255, 0.3) !important; 
} 

/* ============= DIVIDER ============= */
hr { 
    border-color: rgba(0, 255, 255, 0.2) !important; 
    margin: 2rem 0 !important; 
} 

/* ============= HOLOGRAPHIC CONTAINER ============= */
.holographic-container { 
    background: rgba(10, 10, 10, 0.8) !important; 
    border: 1px solid rgba(0, 255, 255, 0.2) !important; 
    border-radius: 15px !important; 
    padding: 1.5rem !important; 
    margin-bottom: 1.5rem !important; 
    position: relative !important; 
    overflow: hidden !important; 
} 

.holographic-container::before { 
    content: '' !important; 
    position: absolute !important; 
    top: -50% !important; 
    left: -50% !important; 
    width: 200% !important; 
    height: 200% !important; 
    background: linear-gradient( 
        0deg,  
        transparent,  
        transparent 30%,  
        rgba(0,255,255,0.1) 
    ) !important; 
    transform: rotate(-45deg) !important; 
    transition: all 0.8s ease !important; 
    opacity: 0 !important; 
    z-index: 1 !important; 
} 

.holographic-container:hover::before { 
    opacity: 1 !important; 
    transform: rotate(-45deg) translateY(100%) !important; 
} 

/* ============= CAPTCHA STYLES ============= */
.captcha-container { 
    border: 2px solid #ff6b6b; 
    border-radius: 10px; 
    padding: 15px; 
    margin: 10px 0; 
    background: #1a1a1a; 
} 

.captcha-warning { 
    color: #ff6b6b; 
    font-weight: bold; 
} 

.captcha-success { 
    color: #4CAF50; 
    font-weight: bold; 
} 

/* Status indicators */
.status-success { color: #4CAF50 !important; }
.status-captcha { color: #ff6b6b !important; }
.status-none { color: #ff9800 !important; }
.status-skipped { color: #9e9e9e !important; }
.status-not-fetched { color: #2196F3 !important; }

/* ============= TOUCH SCREEN OPTIMIZATIONS ============= */
/* Larger tap targets for all interactive elements */
.stButton button {
    min-height: 48px !important;
    min-width: 48px !important;
}

.stTabs [data-baseweb="tab"] {
    min-height: 48px !important;
    padding: 12px 20px !important;
}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div,
[data-testid="stNumberInput"] input {
    min-height: 48px !important;
    font-size: 1rem !important;
}

[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label {
    padding: 8px 4px !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
}

/* Remove desktop-only hover transforms (these cause jitter on touch) */
.holographic-card:hover {
    transform: none !important;
}

.stButton button:hover {
    transform: none !important;
}

/* Keep glow effects but remove movement */
.holographic-card {
    transition: box-shadow 0.3s ease, border-color 0.3s ease !important;
}

/* Larger expander click areas */
div[data-testid="stExpander"] > div:first-child {
    min-height: 52px !important;
    display: flex !important;
    align-items: center !important;
}

/* Touch-friendly sidebar elements */
[data-testid="stSidebar"] .stButton button {
    min-height: 52px !important;
    margin-bottom: 8px !important;
}

/* Prevent accidental zoom on input focus (iOS) */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    font-size: 16px !important;
}

/* Touch-friendly metrics */
.stMetric {
    padding: 1.2rem !important;
}

/* Improved scrolling for touch */
.holographic-container,
.holographic-card,
div[data-testid="stExpanderDetails"] {
    -webkit-overflow-scrolling: touch !important;
}

/* ============= MOUSE-DRAGGABLE SCROLLING ============= */
/* Enable smooth scrolling and cursor indication for scrollable areas */
.scrollable-area,
.holographic-container,
.holographic-card,
div[data-testid="stExpanderDetails"],
div[data-testid="stVerticalBlock"],
.main .block-container {
    scroll-behavior: smooth !important;
    cursor: grab !important;
}

.scrollable-area:active,
.holographic-container:active,
.holographic-card:active {
    cursor: grabbing !important;
}

/* Enable horizontal scroll with mouse wheel for wide tables */
.tech-table-wrapper {
    overflow-x: auto;
    overflow-y: visible;
    max-width: 100%;
    cursor: grab;
}

.tech-table-wrapper:active {
    cursor: grabbing;
}

/* Scrollbar styling for better visibility */
.holographic-container::-webkit-scrollbar,
.holographic-card::-webkit-scrollbar,
.tech-table-wrapper::-webkit-scrollbar {
    height: 8px;
    width: 8px;
}

.holographic-container::-webkit-scrollbar-track,
.holographic-card::-webkit-scrollbar-track,
.tech-table-wrapper::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
}

.holographic-container::-webkit-scrollbar-thumb,
.holographic-card::-webkit-scrollbar-thumb,
.tech-table-wrapper::-webkit-scrollbar-thumb {
    background: rgba(0, 255, 255, 0.3);
    border-radius: 4px;
}

.holographic-container::-webkit-scrollbar-thumb:hover,
.holographic-card::-webkit-scrollbar-thumb:hover,
.tech-table-wrapper::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 255, 0.5);
}

/* Patch card touch-friendly */
.patch-card {
    background: rgba(17, 17, 17, 0.95);
    border: 1px solid rgba(0, 255, 255, 0.25);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

/* Orbis patch badge */
.orbis-latest-badge {
    display: inline-block;
    background: linear-gradient(135deg, rgba(0,255,255,0.3), rgba(0,112,204,0.3));
    border: 1px solid rgba(0,255,255,0.5);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: bold;
    color: #0ff;
    text-shadow: 0 0 4px rgba(0,255,255,0.5);
} 

/* ============= USER AGENT DISPLAY ============= */
.user-agent-display {
    font-family: monospace;
    font-size: 0.85rem;
    background: rgba(0, 20, 40, 0.7);
    border: 1px solid rgba(0, 255, 255, 0.3);
    border-radius: 8px;
    padding: 10px;
    margin: 10px 0;
    overflow-x: auto;
    white-space: nowrap;
    color: #8af;
}

.cookie-display {
    font-family: monospace;
    font-size: 0.8rem;
    background: rgba(20, 0, 40, 0.7);
    border: 1px solid rgba(255, 0, 255, 0.3);
    border-radius: 8px;
    padding: 10px;
    margin: 10px 0;
    overflow-x: auto;
    white-space: nowrap;
    color: #f8f;
}

/* ============= INFO BOXES ============= */
.info-box-custom {
    background: rgba(0, 40, 80, 0.3);
    border-left: 4px solid #0ff;
    padding: 15px;
    border-radius: 0 8px 8px 0;
    margin: 15px 0;
}

.warning-box-custom {
    background: rgba(80, 40, 0, 0.3);
    border-left: 4px solid #ff0;
    padding: 15px;
    border-radius: 0 8px 8px 0;
    margin: 15px 0;
}

.success-box-custom {
    background: rgba(0, 80, 40, 0.3);
    border-left: 4px solid #0f0;
    padding: 15px;
    border-radius: 0 8px 8px 0;
    margin: 15px 0;
}

/* ============= CODE BLOCKS ============= */
.code-block {
    font-family: monospace;
    background: rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(0, 255, 255, 0.2);
    border-radius: 5px;
    padding: 10px;
    margin: 5px 0;
    overflow-x: auto;
}

/* ============= TRAFFIC STATUS ============= */
.traffic-status {
    background: rgba(30, 30, 60, 0.8);
    border: 1px solid rgba(0, 150, 255, 0.4);
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    font-family: monospace;
    font-size: 0.85rem;
}

.traffic-success {
    border-left: 4px solid #00ff00;
    background: rgba(0, 60, 0, 0.3);
}

.traffic-warning {
    border-left: 4px solid #ffff00;
    background: rgba(60, 60, 0, 0.3);
}

.traffic-error {
    border-left: 4px solid #ff0000;
    background: rgba(60, 0, 0, 0.3);
}

/* ============= PLATFORM BADGES ============= */
.platform-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: bold;
    margin: 2px;
    text-transform: uppercase;
}

.platform-ps4 {
    background: linear-gradient(135deg, #0070cc, #0033cc);
    color: white;
    border: 1px solid #0055cc;
}

.platform-ps5 {
    background: linear-gradient(135deg, #000000, #333333);
    color: white;
    border: 1px solid #666666;
}

.platform-both {
    background: linear-gradient(135deg, #0070cc, #000000);
    color: white;
    border: 1px solid #444444;
}

.platform-multi {
    background: linear-gradient(135deg, #666666, #333333);
    color: white;
    border: 1px solid #888888;
}

/* ============= RELEASE DATE STYLES ============= */
.release-date-container {
    margin: 5px 0;
    padding: 3px 8px;
    background: rgba(0, 100, 200, 0.2);
    border-radius: 5px;
    display: inline-block;
}

.release-date-label {
    color: #8af;
    font-size: 0.85rem;
    margin-right: 5px;
}

.release-date-value {
    color: #0ff;
    font-weight: bold;
    font-size: 0.9rem;
}
</style>

<script>
// ============= MOUSE-DRAG SCROLLING =============
// Enable grab-to-scroll on holographic containers
document.addEventListener('DOMContentLoaded', function() {
    const scrollableSelectors = [
        '.holographic-container',
        '.holographic-card',
        '.tech-table-wrapper',
        '[data-testid="stExpanderDetails"]'
    ];
    
    scrollableSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            let isDown = false;
            let startX, startY;
            let scrollLeft, scrollTop;
            
            el.addEventListener('mousedown', (e) => {
                // Only enable drag on containers, not on clickable elements
                if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.tagName === 'INPUT') {
                    return;
                }
                isDown = true;
                el.style.cursor = 'grabbing';
                startX = e.pageX - el.offsetLeft;
                startY = e.pageY - el.offsetTop;
                scrollLeft = el.scrollLeft;
                scrollTop = el.scrollTop;
            });
            
            el.addEventListener('mouseleave', () => {
                isDown = false;
                el.style.cursor = 'grab';
            });
            
            el.addEventListener('mouseup', () => {
                isDown = false;
                el.style.cursor = 'grab';
            });
            
            el.addEventListener('mousemove', (e) => {
                if (!isDown) return;
                e.preventDefault();
                const x = e.pageX - el.offsetLeft;
                const y = e.pageY - el.offsetTop;
                const walkX = (x - startX) * 2; // Scroll speed multiplier
                const walkY = (y - startY) * 2;
                el.scrollLeft = scrollLeft - walkX;
                el.scrollTop = scrollTop - walkY;
            });
        });
    });
    
    // Re-apply on Streamlit updates
    const observer = new MutationObserver(() => {
        scrollableSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el.dataset.dragScrollEnabled) return;
                el.dataset.dragScrollEnabled = 'true';
                // Repeat the event listeners setup
                let isDown = false;
                let startX, startY, scrollLeft, scrollTop;
                el.addEventListener('mousedown', (e) => {
                    if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.tagName === 'INPUT') return;
                    isDown = true;
                    el.style.cursor = 'grabbing';
                    startX = e.pageX - el.offsetLeft;
                    startY = e.pageY - el.offsetTop;
                    scrollLeft = el.scrollLeft;
                    scrollTop = el.scrollTop;
                });
                el.addEventListener('mouseleave', () => { isDown = false; el.style.cursor = 'grab'; });
                el.addEventListener('mouseup', () => { isDown = false; el.style.cursor = 'grab'; });
                el.addEventListener('mousemove', (e) => {
                    if (!isDown) return;
                    e.preventDefault();
                    const x = e.pageX - el.offsetLeft;
                    const y = e.pageY - el.offsetTop;
                    const walkX = (x - startX) * 2;
                    const walkY = (y - startY) * 2;
                    el.scrollLeft = scrollLeft - walkX;
                    el.scrollTop = scrollTop - walkY;
                });
            });
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
});
</script>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'parser_initialized': False,
        'parser': None,
        'parser_headless': True,
        'psn_region': 'fi-fi',
        'search_history': [],
        'current_results': None,
        'captcha_challenge': None,
        'show_debug': False,
        'search_in_progress': False,
        'initialization_method': 'automatic',  # 'automatic' or 'cookie'
        'steamdb_cookie_used': False,
        'cf_clearance_cookie': None,
        'cookie_domain': 'steamdb.info',
        'cookie_persist': True,
        'scraper_imported': False,
        'custom_user_agent': None,
        'user_agent_tied_to_cookie': False,
        'steamdb_headers': None,
        'last_request_time': None,
        'platform_filter': 'both',  # NEW: 'ps4', 'ps5', or 'both'
        'enable_psn_search': True,  # NEW: Toggle for PSN search
        'fetch_release_dates': True  # NEW: Toggle for fetching release dates
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Import the scraper module
try:
    from psn_steamdbv2 import SteamDBSeleniumParser, PSNScraper
    st.session_state.scraper_imported = True
except Exception as e:
    st.error(f"Failed to import scraper modules: {e}")
    st.session_state.scraper_imported = False

# ===========================================
# RELEASE DATE EXTRACTION FUNCTION
# ===========================================

def extract_release_date_from_psn_page(html_content):
    """
    Extract release date from PSN store page HTML with flexible layout.
    Handles different languages and responsive designs.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Strategy 1: Look for the release date using data-qa attributes
        release_date_key = None
        
        # Find all dt elements that might contain release date label
        dt_elements = soup.find_all('dt')
        
        # Possible release date keys in different languages
        # Finnish: "Julkaisu:", English: "Release Date:", etc.
        release_date_labels = [
            'Julkaisu:', 'Julkaisu', 'Release Date:', 'Release Date',
            'Release:', 'Release', 'Data di pubblicazione:', '発売日:',
            'Fecha de lanzamiento:', 'Veröffentlichungsdatum:',
            'Дата выхода:', '출시일:', 'تاريخ الإصدار:'
        ]
        
        # Look for matching dt element
        for dt in dt_elements:
            dt_text = dt.get_text(strip=True)
            if any(label.lower() in dt_text.lower() for label in release_date_labels):
                # Found the label, now get the corresponding dd element
                parent = dt.parent
                if parent:
                    # Find the next dd element after this dt
                    dt_index = dt.parent.findChildren().index(dt) if dt.parent else -1
                    if dt_index != -1:
                        children = parent.findChildren()
                        if dt_index + 1 < len(children):
                            dd = children[dt_index + 1]
                            release_date = dd.get_text(strip=True)
                            if release_date:
                                # Clean up the date format
                                release_date = release_date.replace('\n', ' ').strip()
                                return release_date
        
        # Strategy 2: Look for data-qa attributes specifically for release date
        release_dd = soup.find('dd', {'data-qa': 'gameInfo#releaseInformation#releaseDate-value'})
        if release_dd:
            release_date = release_dd.get_text(strip=True)
            if release_date:
                return release_date
        
        # Strategy 3: Look for platform release date section
        release_section = soup.find('dl', {'data-qa': 'gameInfo#releaseInformation'})
        if release_section:
            # Find all dt/dd pairs
            dts = release_section.find_all('dt')
            dds = release_section.find_all('dd')
            
            for dt, dd in zip(dts, dds):
                dt_text = dt.get_text(strip=True)
                if any(label.lower() in dt_text.lower() for label in release_date_labels):
                    release_date = dd.get_text(strip=True)
                    if release_date:
                        return release_date
        
        # Strategy 4: Search for date patterns in the game info section
        date_patterns = [
            r'\d{1,2}\.\d{1,2}\.\d{4}',  # dd.mm.yyyy (Finnish format)
            r'\d{4}-\d{2}-\d{2}',        # yyyy-mm-dd
            r'\d{1,2}/\d{1,2}/\d{4}',    # mm/dd/yyyy
            r'\d{1,2}\s+[A-Za-zäöüß]+\s+\d{4}',  # 20 October 2023
        ]
        
        # Search in the game info section
        game_info = soup.find('div', {'data-qa': 'gameInfo'})
        if game_info:
            text_content = game_info.get_text()
            for pattern in date_patterns:
                match = re.search(pattern, text_content)
                if match:
                    return match.group()
        
        return None
        
    except Exception as e:
        print(f"Error extracting release date: {e}")
        return None

# ===========================================
# STEAMDB CF_CLEARANCE COOKIE + USER AGENT FUNCTIONS
# ===========================================

def generate_rum_data(page_url, pageload_id=None, event_type=1):
    """Generate RUM (Real User Monitoring) data for SteamDB"""
    if pageload_id is None:
        pageload_id = str(uuid.uuid4())
    
    current_time = int(time.time() * 1000)
    start_time = current_time - random.randint(200, 800)
    
    # Generate realistic timing data
    first_paint = random.randint(250, 450)
    ttfb = random.randint(80, 230)  # Time to First Byte
    
    rum_data = {
        "memory": {
            "totalJSHeapSize": random.randint(30000000, 60000000),
            "usedJSHeapSize": random.randint(25000000, 50000000),
            "jsHeapSizeLimit": 4294967296
        },
        "resources": [],
        "referrer": "",
        "eventType": event_type,
        "firstPaint": first_paint,
        "firstContentfulPaint": first_paint,
        "startTime": start_time,
        "versions": {
            "fl": "2024.11.0",
            "js": "2024.6.1",
            "timings": 2
        },
        "pageloadId": pageload_id,
        "location": page_url,
        "nt": "reload" if event_type == 1 else "navigate",
        "timingsV2": {
            "unloadEventStart": random.randint(80, 240),
            "unloadEventEnd": random.randint(80, 240),
            "domInteractive": random.randint(350, 500),
            "domContentLoadedEventStart": random.randint(360, 510),
            "domContentLoadedEventEnd": random.randint(360, 510),
            "domComplete": random.randint(390, 560),
            "loadEventStart": random.randint(390, 560),
            "loadEventEnd": random.randint(391, 561),
            "type": "reload" if event_type == 1 else "navigate",
            "redirectCount": 0,
            "criticalCHRestart": 0,
            "activationStart": 0,
            "initiatorType": "navigation",
            "nextHopProtocol": "h2",
            "deliveryType": "",
            "workerStart": 0,
            "redirectStart": 0,
            "redirectEnd": 0,
            "fetchStart": random.uniform(0.8, 1.2),
            "domainLookupStart": random.uniform(0.8, 1.2),
            "domainLookupEnd": random.uniform(0.8, 1.2),
            "connectStart": random.uniform(1, 7),
            "connectEnd": random.uniform(100, 120),
            "secureConnectionStart": random.uniform(50, 60),
            "requestStart": random.uniform(110, 120),
            "responseStart": ttfb,
            "responseEnd": ttfb + random.randint(5, 15),
            "transferSize": random.randint(33000, 34000),
            "encodedBodySize": random.randint(32800, 33200),
            "decodedBodySize": random.randint(268000, 269000),
            "responseStatus": 200,
            "finalResponseHeadersStart": ttfb,
            "firstInterimResponseStart": 0,
            "workerRouterEvaluationStart": 0,
            "workerCacheLookupStart": 0,
            "workerMatchedSourceType": "",
            "workerFinalSourceType": "",
            "renderBlockingStatus": "non-blocking",
            "contentEncoding": "zstd",
            "name": page_url,
            "entryType": "navigation",
            "startTime": 0,
            "duration": random.randint(380, 600)
        },
        "dt": "",
        "siteToken": "91efbe05a59742ddadf5d555608bbe98",
        "st": 2 if event_type == 1 else 1
    }
    
    # Add LCP, FID, CLS data for event_type 3
    if event_type == 3:
        rum_data.update({
            "landingPath": page_url,
            "lcp": {
                "value": first_paint,
                "path": page_url,
                "element": "div.container>div.row.app-row>div.span8>table.table.table-bordered.table-responsive-flex>tbody>tr>td",
                "size": random.randint(8000, 8500),
                "rld": 0,
                "rlt": 0,
                "erd": random.uniform(200, 220),
                "fp": None
            },
            "fid": {"value": -1},
            "cls": {"value": 0, "path": page_url},
            "fcp": {"value": first_paint, "path": page_url},
            "ttfb": {"value": ttfb, "path": page_url},
            "inp": {"value": -1}
        })
    
    return rum_data

def setup_steamdb_headers(user_agent, cf_clearance_cookie):
    """Setup realistic SteamDB headers including all sec-ch-ua headers"""
    timestamp = int(time.time())
    
    # Chrome 144 specific headers
    headers = {
        'Host': 'steamdb.info',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-full-version': '144.0.7559.133',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"19.0.0"',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version-list': '"Not(A:Brand";v="8.0.0.0", "Chromium";v="144.0.7559.133", "Google Chrome";v="144.0.7559.133"',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': f'cf_clearance={cf_clearance_cookie}',
        'Priority': 'u=0, i'
    }
    
    return headers

def setup_steamdb_api_headers(user_agent, cf_clearance_cookie, referer):
    """Setup headers for SteamDB API/RUM requests"""
    headers = {
        'Host': 'steamdb.info',
        'Connection': 'keep-alive',
        'sec-ch-ua-full-version-list': '"Not(A:Brand";v="8.0.0.0", "Chromium";v="144.0.7559.133", "Google Chrome";v="144.0.7559.133"',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version': '144.0.7559.133',
        'User-Agent': user_agent,
        'Content-Type': 'application/json',
        'sec-ch-ua-platform-version': '"19.0.0"',
        'Accept': '*/*',
        'Origin': 'https://steamdb.info',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': referer,
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': f'cf_clearance={cf_clearance_cookie}',
        'Priority': 'u=1, i'
    }
    
    return headers

def simulate_real_traffic(session, page_url, cf_clearance_cookie, user_agent, show_status=True):
    """
    Simulate real browser traffic pattern for SteamDB
    Returns: (success, response, pageload_id)
    """
    try:
        pageload_id = str(uuid.uuid4())
        
        # 1. Send initial GET request
        if show_status:
            st.info(f"📡 Sending initial GET request to: {page_url}")
        
        headers = setup_steamdb_headers(user_agent, cf_clearance_cookie)
        response1 = session.get(page_url, headers=headers)
        
        # Check for 451 status (blocked)
        if response1.status_code == 451:
            if show_status:
                st.warning(f"⚠️ Received 451 status (blocked). Sending RUM data...")
            
            # Send RUM data even if blocked
            rum_headers = setup_steamdb_api_headers(user_agent, cf_clearance_cookie, page_url)
            rum_data = generate_rum_data(page_url, pageload_id, event_type=1)
            
            try:
                rum_response = session.post(
                    "https://steamdb.info/cdn-cgi/rum?",
                    headers=rum_headers,
                    json=rum_data
                )
                if show_status:
                    st.info(f"📊 Sent RUM data (status: {rum_response.status_code})")
            except:
                pass
            
            return False, response1, pageload_id
        
        # 2. Send first RUM data (eventType: 1)
        if show_status:
            st.info("📊 Sending first RUM data (eventType: 1)")
        
        rum_headers1 = setup_steamdb_api_headers(user_agent, cf_clearance_cookie, page_url)
        rum_data1 = generate_rum_data(page_url, pageload_id, event_type=1)
        
        response2 = session.post(
            "https://steamdb.info/cdn-cgi/rum?",
            headers=rum_headers1,
            json=rum_data1
        )
        
        # 3. Send second RUM data (eventType: 3)
        if show_status:
            st.info("📊 Sending second RUM data (eventType: 3)")
        
        rum_headers2 = setup_steamdb_api_headers(user_agent, cf_clearance_cookie, page_url)
        rum_data2 = generate_rum_data(page_url, pageload_id, event_type=3)
        
        response3 = session.post(
            "https://steamdb.info/cdn-cgi/rum?",
            headers=rum_headers2,
            json=rum_data2
        )
        
        # Update last request time
        st.session_state.last_request_time = time.time()
        
        if show_status:
            st.success(f"✅ Real traffic simulation complete")
            st.markdown(f"""
            <div class="traffic-status traffic-success">
            <strong>Traffic Pattern:</strong><br>
            1. GET {page_url} ({response1.status_code})<br>
            2. POST /cdn-cgi/rum (eventType: 1) ({response2.status_code})<br>
            3. POST /cdn-cgi/rum (eventType: 3) ({response3.status_code})
            </div>
            """, unsafe_allow_html=True)
        
        return True, response1, pageload_id
        
    except Exception as e:
        if show_status:
            st.error(f"❌ Error simulating real traffic: {e}")
        return False, None, None

def setup_with_steamdb_cookie_and_ua():
    """
    Allow user to manually input cf_clearance cookie for SteamDB and User Agent
    Returns: (success, message) tuple
    """
    with st.container():
        st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
        st.markdown("### 🔐 SteamDB Cloudflare Bypass")
        
        # Cookie input form
        with st.form("steamdb_cookie_form"):
            st.markdown("""
            **⚠️ IMPORTANT:** This cookie is **ONLY for SteamDB** (steamdb.info), not for PSN Store.
            
            **Instructions:**
            1. Visit [https://steamdb.info](https://steamdb.info) in a browser
            2. Solve the Cloudflare challenge manually
            3. Get BOTH from browser developer tools (F12):
               - **User Agent:** From Network tab → Headers → User-Agent
               - **cf_clearance cookie:** From Application/Storage → Cookies → steamdb.info
            4. Paste both values below
            """)
            
            # Example section
            with st.expander("📋 Example (Click to see correct format)"):
                st.markdown("**Correct User Agent format:**")
                st.code("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36", language="text")
                
                st.markdown("**Correct Cookie format (just the value part):**")
                st.code("1IeuwCI37BAAFDMEkChbWBkggs5wEXy7t0NXfrAsuUE-1770571990-1.2.1.1-wuWPVlnL7wpgB1QAbPeqSexIzjC.nnxvAocZm1INlBeqwMokVol.b.scj4wfDHRqNkRAyXiULn5uNdHuS674V5FXACEemTJksguTnHScz_TbEGx9.uU1XemK2BX5OVGSRiIxfYvq03rVvOzQHmZY1xWptXSXi7NwwiALK9iqOjLpnfO1hP5QpHQ7DTlwkwBFgtg7tnQUOH65Pr.TCh68N6u5l7gYfgjnFlOtUPAtarDIuTMtpqKKcNi6zSKD23yj", language="text")
            
            # User Agent input
            st.markdown("---")
            st.markdown("#### 🔧 User Agent (REQUIRED)")
            user_agent = st.text_area(
                "User Agent:",
                placeholder="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
                height=80,
                help="The EXACT User Agent string from your browser"
            )
            
            # Cookie input fields
            st.markdown("---")
            st.markdown("#### 🍪 SteamDB Cloudflare Cookie")
            col1, col2 = st.columns(2)
            
            with col1:
                cookie_value = st.text_input(
                    "cf_clearance cookie value:",
                    placeholder="e.g., 1IeuwCI37BAAFDMEkChbWBkggs5wEXy7t0NXfrAsuUE...",
                    type="password",
                    help="ONLY the cookie value for steamdb.info"
                )
            
            with col2:
                cookie_domain = st.text_input(
                    "Cookie domain:",
                    value="steamdb.info",
                    help="Should be 'steamdb.info' for SteamDB"
                )
            
            # Additional options
            st.markdown("---")
            col3, col4 = st.columns(2)
            with col3:
                use_headless = st.checkbox("Use headless mode", value=True, 
                                          help="Run browser in background")
            with col4:
                persist_cookie = st.checkbox("Persist cookie in session", value=True,
                                            help="Save cookie for future use (valid for 2 hours)")
            
            submitted = st.form_submit_button("🔓 Apply SteamDB Cookie", type="primary", 
                                             use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if submitted:
            if not cookie_value.strip():
                st.error("❌ Please enter the cf_clearance cookie value")
                return False, "No cookie provided"
            
            if not user_agent.strip():
                st.error("❌ Please enter the User Agent")
                return False, "No User Agent provided"
            
            try:
                # Show progress
                progress = st.progress(0)
                status = st.empty()
                
                status.info("🔄 Setting up SteamDB Cloudflare bypass...")
                progress.progress(0.3)
                
                # Clear any existing parser
                if st.session_state.parser:
                    try:
                        st.session_state.parser.close()
                    except:
                        pass
                
                # Create parser with headless mode based on user choice
                st.info(f"📋 Creating parser (headless={use_headless}, region={st.session_state.psn_region})")
                parser = SteamDBSeleniumParser(
                    headless=use_headless, 
                    region=st.session_state.psn_region,
                    platform_filter=st.session_state.platform_filter
                )
                
                # Setup driver first
                status.info("🔧 Setting up Chrome driver...")
                st.info("📝 Check the console/terminal for detailed ChromeDriver setup logs...")
                
                # Add a log viewer expander
                with st.expander("🔍 View ChromeDriver Setup Details", expanded=True):
                    st.markdown("""
                    **ChromeDriver will try these strategies in order:**
                    1. 🌐 webdriver-manager (auto-download from internet)
                    2. 💻 System ChromeDriver (from PATH)
                    3. 📁 Common Windows locations
                    4. 🎯 Default Selenium detection
                    
                    **Check your terminal/console for detailed logs!**
                    """)
                
                setup_success = parser.setup_driver(max_retries=2)
                
                if not setup_success:
                    progress.progress(1.0)
                    status.error("❌ Failed to setup Chrome driver")
                    st.error("""
                    **ChromeDriver Setup Failed!**
                    
                    Check the terminal/console for detailed error messages.
                    
                    **Quick fixes:**
                    1. ✅ Check internet connection (webdriver-manager needs it)
                    2. 📥 Download ChromeDriver manually: https://chromedriver.chromium.org/
                    3. 📂 Place `chromedriver.exe` in: `C:\\chromedriver.exe`
                    4. 🔄 Restart the Streamlit app after placing chromedriver.exe
                    """)
                    return False, "Failed to setup Chrome driver"
                
                st.success("✅ Chrome driver setup successful!")
                progress.progress(0.6)
                
                # Set custom User Agent for the driver
                status.info("Setting User Agent in browser...")
                try:
                    # Update the driver's user agent
                    parser.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                        "userAgent": user_agent
                    })
                    
                    st.success("✅ User Agent set in browser")
                    
                except Exception as e:
                    st.warning(f"⚠️ Could not set User Agent via CDP: {e}")
                
                # Add the cf_clearance cookie to SteamDB domain
                status.info("Adding SteamDB Cloudflare cookie...")
                try:
                    # Navigate to SteamDB first to set cookie in correct context
                    parser.driver.get("https://steamdb.info")
                    time.sleep(2)
                    
                    # Clear existing cookies first
                    parser.driver.delete_all_cookies()
                    time.sleep(1)
                    
                    # Add the cf_clearance cookie for SteamDB
                    cookie_dict = {
                        'name': 'cf_clearance',
                        'value': cookie_value,
                        'domain': cookie_domain,
                        'path': '/',
                        'secure': True,
                        'httpOnly': True,
                        'sameSite': 'Lax'
                    }
                    
                    parser.driver.add_cookie(cookie_dict)
                    
                    progress.progress(0.8)
                    st.success("✅ Cookie added to browser!")
                    
                    # Generate realistic headers for SteamDB
                    steamdb_headers = setup_steamdb_headers(user_agent, cookie_value)
                    st.session_state.steamdb_headers = steamdb_headers
                    
                    # Update the parser's session with realistic headers
                    for key, value in steamdb_headers.items():
                        if key.lower() != 'host':  # Don't override Host header
                            parser.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                                'headers': {key: value}
                            })
                    
                except Exception as e:
                    st.warning(f"⚠️ Cookie addition note: {e}")
                
                # Test the cookie by simulating real traffic
                status.info("Testing SteamDB Cloudflare bypass...")
                try:
                    test_url = "https://steamdb.info/app/2523720/"  # Test with a real app page
                    
                    # Create a requests session for testing
                    import requests
                    test_session = requests.Session()
                    
                    # Test with real traffic simulation
                    success, response, pageload_id = simulate_real_traffic(
                        test_session, 
                        test_url, 
                        cookie_value, 
                        user_agent,
                        show_status=True
                    )
                    
                    if success:
                        if response and response.status_code == 200:
                            status.success("✅ SteamDB Cloudflare bypass successful!")
                            
                            # Check if we got actual content
                            if 'steamdb' in response.text.lower():
                                st.success("✅ Received valid SteamDB content")
                            else:
                                st.warning("⚠️ Response may not contain expected SteamDB content")
                        else:
                            st.warning("⚠️ Got response but status code not 200")
                    else:
                        if response and response.status_code == 451:
                            st.error("❌ Still getting 451 blocked response even with cookie")
                            st.info("""
                            **Possible issues:**
                            1. Cookie expired or invalid
                            2. User Agent doesn't match
                            3. IP address changed
                            4. Need to solve challenge again
                            """)
                        else:
                            st.warning("⚠️ Cloudflare bypass test had issues")
                    
                    progress.progress(1.0)
                    
                    # Store parser in session state
                    st.session_state.parser = parser
                    st.session_state.parser_initialized = True
                    st.session_state.parser_headless = use_headless
                    st.session_state.steamdb_cookie_used = True
                    st.session_state.initialization_method = 'steamdb_cookie'
                    st.session_state.user_agent_tied_to_cookie = True
                    st.session_state.custom_user_agent = user_agent
                    
                    # Store cookie for persistence if requested
                    if persist_cookie:
                        st.session_state.cf_clearance_cookie = {
                            'value': cookie_value,
                            'domain': cookie_domain,
                            'timestamp': time.time(),
                            'headless': use_headless,
                            'user_agent': user_agent
                        }
                        st.session_state.cookie_persist = True
                    
                    # Clear status displays
                    time.sleep(2)
                    progress.empty()
                    status.empty()
                    
                    return True, "Successfully initialized with SteamDB Cloudflare cookie"
                    
                except Exception as e:
                    parser.close()
                    progress.progress(1.0)
                    status.error(f"❌ Error testing cookie: {str(e)}")
                    return False, f"Error testing cookie: {str(e)}"
                
            except Exception as e:
                return False, f"Error initializing with cookie: {str(e)}"
        
        return False, "Form not submitted"

def initialize_with_stored_steamdb_cookie():
    """
    Initialize parser with stored SteamDB cf_clearance cookie and User Agent if available
    Returns: bool - True if successful
    """
    # Check if cookie exists and is not None
    if ('cf_clearance_cookie' in st.session_state and 
        st.session_state.cf_clearance_cookie is not None):
        cookie_data = st.session_state.cf_clearance_cookie
        
        # Check if cookie is recent (less than 2 hours old)
        cookie_age = time.time() - cookie_data.get('timestamp', 0)
        if cookie_age < 7200:  # 2 hours in seconds
            st.info("🔄 Using stored SteamDB Cloudflare cookie...")
            
            try:
                # Clear any existing parser
                if st.session_state.parser:
                    try:
                        st.session_state.parser.close()
                    except:
                        pass
                
                # Get headless mode preference from cookie or default
                headless_mode = cookie_data.get('headless', st.session_state.parser_headless)
                
                # Create new parser
                parser = SteamDBSeleniumParser(
                    headless=headless_mode,
                    region=st.session_state.psn_region,
                    platform_filter=st.session_state.platform_filter
                )
                
                # Setup driver with the cookie
                st.info("🔧 Setting up driver with stored SteamDB cookie...")
                st.info("📝 Check the console/terminal for detailed ChromeDriver setup logs...")
                
                if not parser.setup_driver(max_retries=2):
                    st.error("❌ Failed to setup Chrome driver")
                    st.error("""
                    **ChromeDriver Setup Failed!**
                    
                    Check the terminal/console for detailed error messages.
                    
                    **Possible solutions:**
                    1. Download ChromeDriver: https://chromedriver.chromium.org/
                    2. Place it in: C:\\chromedriver.exe
                    3. Or check internet connection for webdriver-manager
                    """)
                    return False
                
                # Set User Agent if stored
                user_agent = cookie_data.get('user_agent')
                if user_agent:
                    try:
                        parser.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                            "userAgent": user_agent
                        })
                        st.success(f"✅ Applied stored User Agent")
                    except Exception as e:
                        st.warning(f"⚠️ Could not set User Agent via CDP: {e}")
                
                # Add the cookie for SteamDB
                try:
                    parser.driver.get("https://steamdb.info")
                    time.sleep(2)
                    
                    parser.driver.add_cookie({
                        'name': 'cf_clearance',
                        'value': cookie_data['value'],
                        'domain': cookie_data.get('domain', 'steamdb.info'),
                        'path': '/',
                        'secure': True,
                        'httpOnly': True,
                        'sameSite': 'Lax'
                    })
                    
                    # Generate and store realistic headers
                    steamdb_headers = setup_steamdb_headers(user_agent, cookie_data['value'])
                    st.session_state.steamdb_headers = steamdb_headers
                    
                except Exception as e:
                    st.warning(f"⚠️ Could not add cookie to driver: {e}")
                
                # Store parser in session state
                st.session_state.parser = parser
                st.session_state.parser_initialized = True
                st.session_state.parser_headless = headless_mode
                st.session_state.steamdb_cookie_used = True
                st.session_state.initialization_method = 'steamdb_cookie'
                st.session_state.user_agent_tied_to_cookie = bool(user_agent)
                if user_agent:
                    st.session_state.custom_user_agent = user_agent
                
                st.success("✅ Initialized with stored SteamDB cookie!")
                return True
                    
            except Exception as e:
                st.error(f"❌ Error using stored cookie: {e}")
                return False
        else:
            st.warning("⚠️ Stored cookie has expired (older than 2 hours). Please get a new one.")
            # Clear expired cookie
            st.session_state.cf_clearance_cookie = None
            st.session_state.custom_user_agent = None
            st.session_state.steamdb_headers = None
            return False
    
    return False

def initialize_automatically():
    """
    Initialize parser automatically
    Returns: bool - True if successful
    """
    try:
        # Clear any existing parser
        if st.session_state.parser:
            try:
                st.session_state.parser.close()
            except:
                pass
        
        # Initialize parser
        st.session_state.parser = SteamDBSeleniumParser(
            headless=st.session_state.parser_headless,
            region=st.session_state.psn_region,
            platform_filter=st.session_state.platform_filter
        )
        
        # Setup driver
        with st.spinner("Setting up Chrome browser..."):
            success = st.session_state.parser.setup_driver_with_turnstile()
            
            if success:
                st.session_state.parser_initialized = True
                st.session_state.initialization_method = 'automatic'
                st.session_state.steamdb_cookie_used = False
                st.session_state.user_agent_tied_to_cookie = False
                st.session_state.custom_user_agent = None
                st.session_state.steamdb_headers = None
                st.success("✅ Parser initialized automatically!")
                return True
            else:
                st.error("❌ Failed to initialize automatically. Try SteamDB cookie method.")
                st.session_state.parser = None
                return False
                
    except Exception as e:
        st.error(f"❌ Error during automatic initialization: {str(e)}")
        st.session_state.parser = None
        return False

def show_instructions_get_steamdb_cookie():
    """Show detailed instructions for getting SteamDB cookie and User Agent"""
    with st.expander("📖 Detailed Instructions: How to Get SteamDB Cookie & User Agent"):
        st.markdown("""
        ### Step-by-Step Guide for SteamDB ONLY
        
        **1. Open Chrome/Firefox Browser**
        - Use a regular browser (not incognito)
        - Make sure you're on the same network/IP as you'll use for scraping
        
        **2. Visit SteamDB**
        - Go to: https://steamdb.info
        - You should see a Cloudflare challenge page
        - Complete the challenge (click "Verify you are human" or similar)
        
        **3. Open Developer Tools**
        - Press **F12** or **Ctrl+Shift+I**
        - Or right-click → "Inspect"
        
        **4. Get the User Agent**
        - Go to the **Network** tab
        - Refresh the page (F5)
        - Click on any request to `steamdb.info`
        - In the **Headers** tab, find **User-Agent** in Request Headers
        - Copy the ENTIRE User Agent string
        - Example: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36`
        
        **5. Get the cf_clearance Cookie**
        - Go to the **Application** tab (Chrome) or **Storage** tab (Firefox)
        - Expand **Cookies** → **https://steamdb.info**
        - Find the `cf_clearance` cookie
        - Copy ONLY the **Value** (not the name)
        - Example: `1IeuwCI37BAAFDMEkChbWBkggs5wEXy7t0NXfrAsuUE-1770571990-1.2.1.1-wuWPVlnL7wpgB1QAbPeqSexIzjC.nnxvAocZm1INlBeqwMokVol.b.scj4wfDHRqNkRAyXiULn5uNdHuS674V5FXACEemTJksguTnHScz_TbEGx9.uU1XemK2BX5OVGSRiIxfYvq03rVvOzQHmZY1xWptXSXi7NwwiALK9iqOjLpnfO1hP5QpHQ7DTlwkwBFgtg7tnQUOH65Pr.TCh68N6u5l7gYfgjnFlOtUPAtarDIuTMtpqKKcNi6zSKD23yj`
        
        **6. Paste Both Values in the Form Above**
        - User Agent → "User Agent" field
        - Cookie value → "cf_clearance cookie value" field
        - Click "Apply SteamDB Cookie"
        
        ### ⚠️ Important Notes
        
        **SteamDB Only:**
        - This cookie is ONLY for steamdb.info
        - It will NOT work for store.playstation.com
        - PSN Store scraping uses different methods
        
        **Cookie-User Agent Binding:**
        - Cloudflare ties cookies to specific User Agents
        - Using a different User Agent will invalidate the cookie
        - Always use the EXACT User Agent from the same browser session
        
        **Real Traffic Simulation:**
        - After setting cookie, the system simulates real browser traffic
        - Sends RUM (Real User Monitoring) data like real browsers
        - Includes proper headers and timing data
        
        **Cookie Lifespan:**
        - Cookies typically last 1-2 hours
        - May expire faster with heavy usage
        - Get a new cookie when scraping stops working
        """)

# ===========================================
# MAIN APP LAYOUT
# ===========================================

# Main title
st.markdown('<h1 class="main-header">🎮 SteamDB & PSN Game Matcher</h1>', unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # Platform filter toggle (NEW)
    st.markdown("#### 🎮 Platform Filter")
    platform_col1, platform_col2, platform_col3 = st.columns(3)
    
    with platform_col1:
        ps4_selected = st.checkbox(
            "PS4", 
            value="ps4" in st.session_state.platform_filter or st.session_state.platform_filter == "both",
            disabled=st.session_state.search_in_progress,
            key="ps4_checkbox"
        )
    
    with platform_col2:
        ps5_selected = st.checkbox(
            "PS5", 
            value="ps5" in st.session_state.platform_filter or st.session_state.platform_filter == "both",
            disabled=st.session_state.search_in_progress,
            key="ps5_checkbox"
        )
    
    with platform_col3:
        enable_psn = st.checkbox(
            "PSN", 
            value=st.session_state.enable_psn_search,
            disabled=st.session_state.search_in_progress,
            key="enable_psn_checkbox",
            help="Enable/disable PSN search"
        )
    
    # Determine platform filter based on checkboxes
    if ps4_selected and ps5_selected:
        platform_filter = "both"
    elif ps4_selected:
        platform_filter = "ps4"
    elif ps5_selected:
        platform_filter = "ps5"
    else:
        platform_filter = "none"
    
    st.session_state.platform_filter = platform_filter
    st.session_state.enable_psn_search = enable_psn
    
    # Display current filter status
    filter_status = {
        "both": "🔍 Searching PS4 & PS5",
        "ps4": "🎮 PS4 only",
        "ps5": "🎮 PS5 only",
        "none": "⚠️ No platform"
    }
    
    st.info(f"**{filter_status.get(platform_filter, 'Custom')}**")
    
    if platform_filter == "none" and enable_psn:
        st.warning("Select PS4/PS5 to enable PSN search!")
        st.session_state.enable_psn_search = False
    
    st.markdown("---")
    
    # Release date toggle (NEW)
    st.markdown("#### 📅 Release Dates")
    fetch_release_dates = st.checkbox(
        "Fetch release dates", 
        value=st.session_state.get('fetch_release_dates', True),
        disabled=st.session_state.search_in_progress,
        key="fetch_release_dates_checkbox",
        help="Fetch release dates for PSN games (adds extra requests)"
    )
    st.session_state.fetch_release_dates = fetch_release_dates
    
    if fetch_release_dates:
        st.info("Release dates will be fetched for PSN games")
    else:
        st.info("Release dates will not be fetched")
    
    st.markdown("---")
    
    # Initialization method selector
    st.markdown("#### Initialization Method")
    init_method = st.radio(
        "Choose initialization method:",
        ["Automatic (Recommended but all functions won't work with this at the same time)", "SteamDB Cookie + User Agent"],
        index=0 if st.session_state.initialization_method == 'automatic' else 1,
        horizontal=False,
        key="init_method_selector"
    )
    
    st.markdown("---")
    
    if init_method == "SteamDB Cookie + User Agent":
        # Show instructions button
        if st.button("📖 Show Instructions", use_container_width=True):
            show_instructions_get_steamdb_cookie()
        
        # Show cookie bypass section
        if not st.session_state.parser_initialized or st.session_state.initialization_method != 'steamdb_cookie':
            # Show cookie input form
            st.markdown("#### 🔐 SteamDB Cloudflare Setup")
            
            # Check for stored cookie first - Added None check
            if ('cf_clearance_cookie' in st.session_state and 
                st.session_state.cf_clearance_cookie is not None):
                cookie_age = time.time() - st.session_state.cf_clearance_cookie.get('timestamp', 0)
                age_minutes = int(cookie_age // 60)
                
                if age_minutes < 120:  # Less than 2 hours
                    st.info(f"✅ Stored SteamDB bypass available ({age_minutes} minutes ago)")
                    
                    # Show stored User Agent if available
                    stored_ua = st.session_state.cf_clearance_cookie.get('user_agent')
                    if stored_ua:
                        with st.expander("View stored User Agent"):
                            st.markdown('<div class="user-agent-display">', unsafe_allow_html=True)
                            st.text(stored_ua[:80] + "..." if len(stored_ua) > 80 else stored_ua)
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Use Stored", use_container_width=True,
                                   disabled=st.session_state.search_in_progress):
                            if initialize_with_stored_steamdb_cookie():
                                st.rerun()
                    
                    with col2:
                        if st.button("🗑️ Clear", use_container_width=True,
                                   disabled=st.session_state.search_in_progress):
                            st.session_state.cf_clearance_cookie = None
                            st.session_state.custom_user_agent = None
                            st.session_state.steamdb_headers = None
                            st.success("Cleared!")
                            st.rerun()
                    
                    st.markdown("---")
            
            # Show manual cookie + UA input
            success, message = setup_with_steamdb_cookie_and_ua()
            if success:
                st.rerun()
            elif message != "Form not submitted":
                st.error(f"❌ {message}")
        
        # If already initialized with cookie, show status
        elif st.session_state.parser_initialized and st.session_state.initialization_method == 'steamdb_cookie':
            st.success("✅ Initialized with SteamDB Cloudflare bypass")
            
            # Show User Agent info if available
            if st.session_state.get('custom_user_agent'):
                with st.expander("🔧 Current User Agent"):
                    st.markdown('<div class="user-agent-display">', unsafe_allow_html=True)
                    ua = st.session_state.custom_user_agent
                    st.text(ua[:80] + "..." if len(ua) > 80 else ua)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Show traffic simulation status
            if st.session_state.get('last_request_time'):
                time_since = int(time.time() - st.session_state.last_request_time)
                if time_since < 60:
                    st.info(f"🔄 Last real traffic: {time_since}s ago")
            
            # FIXED: Added None check
            if ('cf_clearance_cookie' in st.session_state and 
                st.session_state.cf_clearance_cookie is not None):
                cookie_age = time.time() - st.session_state.cf_clearance_cookie.get('timestamp', 0)
                age_minutes = int(cookie_age // 60)
                st.info(f"SteamDB bypass age: {age_minutes} minutes")
            
            if st.button("🔄 Reinitialize", use_container_width=True,
                        disabled=st.session_state.search_in_progress):
                if initialize_with_stored_steamdb_cookie():
                    st.rerun()
    
    # Regular configuration (for automatic mode)
    else:
        # Headless mode toggle
        headless_mode = st.toggle(
            "Headless Mode", 
            value=st.session_state.parser_headless, 
            help="Run browser in background (recommended for servers)",
            disabled=st.session_state.search_in_progress
        )
        
        # PSN Region selector
        psn_region = st.selectbox(
            "PSN Region:",
            ["fi-fi", "en-us", "en-gb", "de-de", "fr-fr", "ja-jp"],
            index=["fi-fi", "en-us", "en-gb", "de-de", "fr-fr", "ja-jp"].index(st.session_state.psn_region),
            disabled=st.session_state.search_in_progress
        )
        
        # Update session state
        st.session_state.parser_headless = headless_mode
        st.session_state.psn_region = psn_region
    
    st.markdown("---")
    st.markdown("### 🔧 Parser Setup")
    
    init_col1, init_col2 = st.columns(2)
    
    with init_col1:
        if st.button("🚀 Initialize", type="primary", use_container_width=True, 
                    disabled=st.session_state.search_in_progress):
            if init_method == "SteamDB Cookie + User Agent":
                # Show cookie form if not already initialized
                if not st.session_state.parser_initialized:
                    st.info("Please use the form above to initialize with SteamDB cookie and User Agent")
                else:
                    st.success("✅ Already initialized with SteamDB bypass")
            else:
                # Automatic initialization
                if initialize_automatically():
                    st.rerun()
    
    with init_col2:
        if st.button("🗑️ Clear", type="secondary", use_container_width=True,
                    disabled=st.session_state.search_in_progress):
            if st.session_state.parser:
                try:
                    st.session_state.parser.close()
                    st.success("✅ Parser cleared!")
                except Exception as e:
                    st.error(f"Error clearing parser: {e}")
            
            st.session_state.parser = None
            st.session_state.parser_initialized = False
            st.session_state.current_results = None
            st.session_state.steamdb_cookie_used = False
            st.session_state.initialization_method = 'automatic'
            st.session_state.user_agent_tied_to_cookie = False
            st.session_state.custom_user_agent = None
            st.session_state.steamdb_headers = None
            
            # Clear stored cookie if exists
            st.session_state.cf_clearance_cookie = None
            
            st.rerun()
    
    # Parser status display
    st.markdown("---")
    st.markdown("### 📊 Parser Status")
    
    if st.session_state.parser_initialized and st.session_state.parser:
        status_color = "🟢"
        status_text = "Ready"
        
        # Show parser info
        parser_info = f"""
        **Status:** {status_color} {status_text}
        **Method:** {'SteamDB Cookie+UA Bypass' if st.session_state.steamdb_cookie_used else 'Automatic'}
        **Mode:** {'Headless' if st.session_state.parser_headless else 'Visible'}
        **Region:** {st.session_state.psn_region}
        **Release Dates:** {'✅ Enabled' if st.session_state.fetch_release_dates else '❌ Disabled'}
        """
        
        # Check if steamdb_cookie_used is True and cookie exists
        if (st.session_state.steamdb_cookie_used and 
            'cf_clearance_cookie' in st.session_state and 
            st.session_state.cf_clearance_cookie is not None):
            cookie_age = time.time() - st.session_state.cf_clearance_cookie.get('timestamp', 0)
            age_minutes = int(cookie_age // 60)
            parser_info += f"\n**Bypass Age:** {age_minutes} minutes"
        
        if st.session_state.get('custom_user_agent'):
            parser_info += f"\n**Custom UA:** ✓ Set"
        
        if st.session_state.get('steamdb_headers'):
            parser_info += f"\n**SteamDB Headers:** ✓ Configured"
        
        st.info(parser_info)
    else:
        st.warning("⚠️ Parser not initialized")
    
    # Quick actions
    st.markdown("---")
    st.markdown("### 🎯 Quick Actions")
    
    if st.button("🔄 Test SteamDB Search", use_container_width=True,
                disabled=not st.session_state.parser_initialized or st.session_state.search_in_progress):
        with st.spinner("Testing SteamDB search..."):
            try:
                # Use requests session to test real traffic simulation
                import requests
                test_session = requests.Session()
                
                # Get cookie value if available
                cookie_value = None
                if ('cf_clearance_cookie' in st.session_state and 
                    st.session_state.cf_clearance_cookie is not None):
                    cookie_value = st.session_state.cf_clearance_cookie.get('value')
                
                user_agent = st.session_state.get('custom_user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                
                if cookie_value:
                    st.info("Testing SteamDB with real traffic simulation...")
                    test_url = "https://steamdb.info/app/2523720/"
                    success, response, pageload_id = simulate_real_traffic(
                        test_session,
                        test_url,
                        cookie_value,
                        user_agent,
                        show_status=True
                    )
                    
                    if success:
                        if response and response.status_code == 200:
                            st.success("✅ SteamDB real traffic test successful!")
                        else:
                            st.warning(f"⚠️ SteamDB test returned status: {response.status_code if response else 'No response'}")
                    else:
                        st.error("❌ SteamDB real traffic test failed")
                else:
                    # Test with Selenium parser
                    test_results = st.session_state.parser.search_steamdb_for_games("test", max_results=3)
                    if test_results:
                        st.success(f"✅ SteamDB search working! Found {len(test_results)} results.")
                    else:
                        st.info("ℹ️ SteamDB search returned no results (expected for 'test' query).")
            except Exception as e:
                st.error(f"❌ SteamDB search test failed: {e}")
    
    if st.button("🧹 Clear Results", use_container_width=True):
        st.session_state.current_results = None
        st.success("Results cleared!")
    
    # SteamDB Cookie+UA management (only show if cookie was used)
    if (st.session_state.steamdb_cookie_used or 
        ('cf_clearance_cookie' in st.session_state and st.session_state.cf_clearance_cookie is not None)):
        st.markdown("---")
        st.markdown("### 🔧 SteamDB Bypass Management")
        
        # Display cookie info if exists
        if ('cf_clearance_cookie' in st.session_state and 
            st.session_state.cf_clearance_cookie is not None):
            cookie_data = st.session_state.cf_clearance_cookie
            cookie_age = time.time() - cookie_data.get('timestamp', 0)
            age_minutes = int(cookie_age // 60)
            age_hours = int(age_minutes // 60)
            
            if age_minutes < 120:
                status = "✅ Valid"
                color = "green"
            else:
                status = "⚠️ Expired"
                color = "orange"
            
            has_ua = "✓ Yes" if cookie_data.get('user_agent') else "✗ No"
            
            st.markdown(f"""
            **Status:** <span style="color:{color}">{status}</span>
            **Age:** {age_hours}h {age_minutes % 60}m
            **Domain:** {cookie_data.get('domain', 'steamdb.info')}
            **User Agent:** {has_ua}
            **Real Traffic:** {'✓ Simulated' if st.session_state.get('last_request_time') else '✗ Not sent'}
            """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Bypass", use_container_width=True,
                        disabled=st.session_state.search_in_progress):
                st.info("""
                **To refresh SteamDB bypass:**
                1. Get new SteamDB cookie + User Agent
                2. Use the form above
                3. Click "Apply SteamDB Cookie"
                """)
        
        with col2:
            if st.button("🗑️ Delete Bypass", use_container_width=True,
                        disabled=st.session_state.search_in_progress):
                st.session_state.cf_clearance_cookie = None
                st.session_state.custom_user_agent = None
                st.session_state.steamdb_headers = None
                st.success("SteamDB bypass data deleted!")
                st.rerun()
    
    # Debug toggle
    st.markdown("---")
    st.session_state.show_debug = st.checkbox("Show Debug Info", value=st.session_state.show_debug,
                                             disabled=st.session_state.search_in_progress)
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.info("""
    **SteamDB & PSN Game Matcher**
    
    Match Steam games with their PSN Store counterparts.
    
    **New Features:**
    - 🆕 Release date scraping for PSN games
    - 🆕 Multiple language support (FI, EN, DE, FR, JP, etc.)
    - 🆕 Responsive layout handling for PSN store
    
    **Existing Features:**
    - Search SteamDB for games
    - Find matching PSN Store listings
    - Compare prices and game types
    - Export results to JSON
    
    **SteamDB-Specific Features:**
    - Real traffic simulation with RUM data
    - Cloudflare bypass with cf_clearance cookies
    - User Agent binding for cookie validity
    - Proper sec-ch-ua headers for SteamDB
    
    **Initialization Methods:**
    1. **Automatic:** Standard browser automation (recommended but all functions won't work with this at the same time)
    2. **SteamDB Cookie+UA:** Use cf_clearance cookie + matching User Agent (for steamdb.info ONLY. All functions works with this at the same time.)
    
    **Important Notes:**
    - SteamDB cookie only works for steamdb.info
    - PSN Store uses separate methods
    - Real traffic simulation mimics browser behavior
    - Release dates are fetched from individual game pages
    """)

# ===========================================
# MAIN CONTENT AREA
# ===========================================

if not st.session_state.parser_initialized:
    # Show initialization prompt with holographic design
    st.markdown('<div class="holographic-card">', unsafe_allow_html=True)
    st.markdown("### ⚠️ Parser Not Initialized")
    
    if st.session_state.initialization_method == 'steamdb_cookie':
        st.markdown("""
        **SteamDB Cookie + User Agent Method Selected:**
        
        Cloudflare ties cookies to specific User Agents. For SteamDB bypass to work, you need:
        
        1. **Get cf_clearance cookie** from steamdb.info ONLY
        2. **Get the EXACT User Agent** from the same browser session
        3. Paste both in the sidebar form
        4. Click "Apply SteamDB Cookie"
        5. System will simulate real browser traffic with RUM data
        
        **Click "Show Instructions" in sidebar for detailed guide.**
        
        **⚠️ IMPORTANT:** This cookie is ONLY for steamdb.info, not for PSN Store! All functions works with this at the same time when configured.
        """)
    else:
        st.markdown("""
        **Automatic Method Selected:**
        
        1. Configure settings in sidebar
        2. Click **"🚀 Initialize"** button
        3. Wait for confirmation
        
        **Troubleshooting:**
        - Ensure Chrome is installed
        - Check internet connection
        - If automatic fails, try SteamDB cookie+UA method
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick start instructions
    st.markdown("### 📋 Quick Start Guide")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 1. Configure
        - Choose initialization method
        - Select PSN region
        - Enable release dates if needed
        - Review settings
        """)
    
    with col2:
        st.markdown("""
        #### 2. Initialize
        - Click initialize button
        - Wait for browser setup
        - Check status panel
        """)
    
    with col3:
        st.markdown("""
        #### 3. Search
        - Enter game name
        - Set search options
        - Click search button
        - View results with release dates
        """)
    
    # Show current status with metrics
    st.markdown("---")
    st.markdown("### 📊 Current Status")
    
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    
    with status_col1:
        st.metric("Parser Status", "❌ Not Initialized")
    
    with status_col2:
        st.metric("Initialization Method", 
                 "SteamDB Cookie" if st.session_state.initialization_method == 'steamdb_cookie' else "Automatic")
    
    with status_col3:
        st.metric("PSN Region", st.session_state.psn_region)
    
    with status_col4:
        st.metric("Release Dates", 
                 "✅ Enabled" if st.session_state.get('fetch_release_dates', True) else "❌ Disabled")
    
    # Import status
    if not st.session_state.get('scraper_imported', False):
        st.error("❌ Failed to import scraper modules. Check that psn_steamdbv2.py is in the same directory.")
    else:
        st.success("✅ Scraper modules imported successfully")
    
else:
    # Parser is initialized - show main interface
    st.markdown('<div class="holographic-card">', unsafe_allow_html=True)
    st.markdown("### ✅ Parser Ready!")
    
    method_info = "SteamDB Bypass (Cookie+UA)" if st.session_state.steamdb_cookie_used else "Automatic"
    
    st.markdown(f"""
    - **Initialization:** {method_info}
    - **Headless Mode:** {'✅ Enabled' if st.session_state.parser_headless else '❌ Disabled'}
    - **PSN Region:** {st.session_state.psn_region}
    - **Release Dates:** {'✅ Enabled' if st.session_state.fetch_release_dates else '❌ Disabled'}
    - **Status:** Ready for search operations
    """)
    
    # Show User Agent info if custom UA is set
    if st.session_state.get('custom_user_agent'):
        with st.expander("🔧 Current User Agent"):
            st.markdown('<div class="user-agent-display">', unsafe_allow_html=True)
            ua = st.session_state.custom_user_agent
            st.text(ua)
            st.markdown('</div>', unsafe_allow_html=True)
            st.caption("This User Agent is tied to your SteamDB cf_clearance cookie")
    
    # Show SteamDB headers info if available
    if st.session_state.get('steamdb_headers'):
        with st.expander("📋 SteamDB Headers Configured"):
            st.markdown('<div class="code-block">', unsafe_allow_html=True)
            for key, value in st.session_state.steamdb_headers.items():
                if key != 'Cookie':  # Don't show full cookie
                    st.text(f"{key}: {value[:80]}{'...' if len(str(value)) > 80 else ''}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Check cookie age
    if (st.session_state.steamdb_cookie_used and 
        'cf_clearance_cookie' in st.session_state and 
        st.session_state.cf_clearance_cookie is not None):
        cookie_age = time.time() - st.session_state.cf_clearance_cookie.get('timestamp', 0)
        age_minutes = int(cookie_age // 60)
        if age_minutes > 60:
            st.warning(f"⚠️ SteamDB cookie is {age_minutes} minutes old. May expire soon.")
    
    # Show last real traffic time
    if st.session_state.get('last_request_time'):
        time_since = int(time.time() - st.session_state.last_request_time)
        if time_since < 300:  # Less than 5 minutes
            st.success(f"🔄 Last real traffic simulation: {time_since}s ago")
        else:
            st.info(f"ℹ️ Last real traffic simulation: {time_since//60} minutes ago")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Main search interface
    st.markdown('<h2 class="holographic-text">🔍 Search for Games</h2>', unsafe_allow_html=True)
    
    # Search tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎮 Game Search", 
        "🔧 Technology Search", 
        "📊 Batch Search", 
        "🎯 Prospero (PS5)",
        "🕹️ Orbis (PS4)",
        "⚙️ Settings"
    ])
    
    with tab1:
        # Single game search in holographic container
        with st.container():
            st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
            
            search_col1, search_col2 = st.columns([3, 1])
            
            with search_col1:
                game_query = st.text_input(
                    "Enter game name:", 
                    placeholder="e.g., Assassin's Creed Valhalla, Cyberpunk 2077, The Witcher 3",
                    key="game_query_input"
                )
            
            with search_col2:
                max_results = st.number_input(
                    "Max results:", 
                    min_value=1, 
                    max_value=100, 
                    value=20,
                    key="max_results_input"
                )
            
            # Search options in holographic card
            st.markdown('<div class="holographic-card">', unsafe_allow_html=True)
            st.markdown("#### Search Options")
            options_col1, options_col2, options_col3, options_col4 = st.columns(4)
            
            with options_col1:
                search_psn = st.checkbox("Search PSN", value=True, key="search_psn_check")
            
            with options_col2:
                search_steamdb = st.checkbox("Search SteamDB", value=True, key="search_steamdb_check")
            
            with options_col3:
                get_technologies = st.checkbox("Get technologies", value=False, key="get_tech_check")
            
            with options_col4:
                find_matches = st.checkbox("Find matches", value=True, key="find_matches_check", 
                                          disabled=not (search_psn and search_steamdb))
            st.markdown('</div>', unsafe_allow_html=True)
            
            # PSN Game Type Filter (prominent placement before search options)
            st.markdown('<div class="holographic-card">', unsafe_allow_html=True)
            st.markdown("#### 🎮 PSN Game Type Filter")
            st.caption("Select which types of content to search for on PSN Store")
            
            type_col1, type_col2, type_col3, type_col4 = st.columns(4)
            
            with type_col1:
                type_full_game = st.checkbox("Full Game", value=True, key="type_full_game")
                type_edition = st.checkbox("Edition", value=False, key="type_edition")
                type_bundle = st.checkbox("Bundle", value=True, key="type_bundle")
            
            with type_col2:
                type_demo = st.checkbox("Demo", value=False, key="type_demo")
                type_trial = st.checkbox("Trial", value=False, key="type_trial")
                type_addon = st.checkbox("Add-on", value=False, key="type_addon")
            
            with type_col3:
                type_premium_addon = st.checkbox("Premium Add-on", value=False, key="type_premium_addon")
                type_theme = st.checkbox("Theme", value=False, key="type_theme")
                type_avatar = st.checkbox("Avatar", value=False, key="type_avatar")
            
            with type_col4:
                type_subscription = st.checkbox("Subscription", value=False, key="type_subscription")
                type_currency = st.checkbox("Virtual Currency", value=False, key="type_currency")
                st.caption("💡 Tip: Full Game is auto-selected")
            
            # Build the list of selected types
            psn_game_types = []
            if type_full_game:
                psn_game_types.append("Full Game")
            if type_edition:
                psn_game_types.append("Edition")
            if type_bundle:
                psn_game_types.append("Bundle")
            if type_demo:
                psn_game_types.append("Demo")
            if type_trial:
                psn_game_types.append("Trial")
            if type_addon:
                psn_game_types.append("Add-on")
            if type_premium_addon:
                psn_game_types.append("Premium Add-on")
            if type_theme:
                psn_game_types.append("Theme")
            if type_avatar:
                psn_game_types.append("Avatar")
            if type_subscription:
                psn_game_types.append("Subscription")
            if type_currency:
                psn_game_types.append("Virtual Currency")
            
            # Show selected count
            if psn_game_types:
                st.info(f"✅ {len(psn_game_types)} type(s) selected: {', '.join(psn_game_types)}")
            else:
                st.warning("⚠️ No game types selected! Please select at least one type.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Advanced options in expander
            with st.expander("⚙️ Advanced Search Options"):
                adv_col1, adv_col2 = st.columns(2)
                
                with adv_col1:
                    st.markdown("**Match Confidence Threshold**")
                
                with adv_col2:
                    min_confidence = st.slider(
                        "Minimum match confidence:",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.6,
                        step=0.05,
                        key="min_confidence_slider"
                    )
            
            # Search button
            search_button = st.button(
                "🔍 Search Game", 
                type="primary", 
                use_container_width=True,
                disabled=st.session_state.search_in_progress or not st.session_state.parser_initialized
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        if search_button:
            if not game_query:
                st.error("❌ Please enter a game name to search.")
            else:
                # Set search in progress flag
                st.session_state.search_in_progress = True
                
                try:
                    # Create progress container
                    progress_container = st.container()
                    
                    with progress_container:
                        # Search progress
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Store results
                        results = {
                            'query': game_query,
                            'timestamp': time.time(),
                            'initialization_method': st.session_state.initialization_method,
                            'steamdb_cookie_used': st.session_state.steamdb_cookie_used,
                            'custom_user_agent': st.session_state.get('custom_user_agent'),
                            'real_traffic_simulated': bool(st.session_state.get('last_request_time')),
                            'fetch_release_dates': st.session_state.fetch_release_dates,
                            'psn_results': [],
                            'steamdb_results': [],
                            'matches': [],
                            'technologies': {}
                        }
                        
                        # Step 1: Search SteamDB (with real traffic simulation if using cookie)
                        if search_steamdb:
                            status_text.info(f"🔍 Searching SteamDB for: '{game_query}'...")
                            progress_bar.progress(0.2)
                            
                            try:
                                # If using SteamDB cookie, simulate real traffic first
                                if st.session_state.steamdb_cookie_used and st.session_state.get('cf_clearance_cookie'):
                                    import requests
                                    test_session = requests.Session()
                                    cookie_value = st.session_state.cf_clearance_cookie['value']
                                    user_agent = st.session_state.get('custom_user_agent', '')
                                    
                                    # Test URL for SteamDB search
                                    test_url = f"https://steamdb.info/search/?q={game_query.replace(' ', '+')}"
                                    success, response, pageload_id = simulate_real_traffic(
                                        test_session,
                                        test_url,
                                        cookie_value,
                                        user_agent,
                                        show_status=True
                                    )
                                    
                                    if not success:
                                        st.warning("⚠️ Real traffic simulation failed, trying regular search...")
                                
                                # Perform actual SteamDB search
                                steamdb_results = st.session_state.parser.search_steamdb_for_games(
                                    game_query,
                                    max_results=max_results
                                )
                                results['steamdb_results'] = steamdb_results
                                
                                if steamdb_results:
                                    status_text.success(f"✅ Found {len(steamdb_results)} SteamDB results")
                                else:
                                    status_text.warning("ℹ️ No SteamDB results found")
                                
                            except Exception as e:
                                status_text.error(f"❌ SteamDB search failed: {str(e)}")
                                results['steamdb_error'] = str(e)
                        
                        # Step 2: Search PSN (with release dates if enabled)
                        if search_psn:
                            status_text.info(f"🔍 Searching PSN for: '{game_query}'...")
                            progress_bar.progress(0.4 if search_steamdb else 0.2)
                            
                            try:
                                # Use search with release dates if enabled
                                if st.session_state.fetch_release_dates:
                                    status_text.info(f"📅 Fetching PSN games with release dates...")
                                    psn_results = st.session_state.parser.search_psn_games_with_release_dates(
                                        game_query, 
                                        max_results=max_results
                                    )
                                else:
                                    psn_results = st.session_state.parser.psn_scraper.search_games_with_pagination(
                                        game_query, 
                                        max_results=max_results
                                    )
                                
                                # Filter by game type if specified
                                if psn_game_types and psn_results:
                                    psn_results = [game for game in psn_results if game.game_type in psn_game_types]
                                
                                results['psn_results'] = [game.to_dict() for game in psn_results]
                                
                                if psn_results:
                                    status_text.success(f"✅ Found {len(psn_results)} PSN results")
                                    # Count how many have release dates
                                    release_date_count = sum(1 for game in psn_results if hasattr(game, 'release_date') and game.release_date)
                                    if release_date_count > 0:
                                        status_text.info(f"📅 Found release dates for {release_date_count} games")
                                else:
                                    status_text.warning("ℹ️ No PSN results found")
                                
                            except Exception as e:
                                status_text.error(f"❌ PSN search failed: {str(e)}")
                                results['psn_error'] = str(e)
                        
                        # Step 3: Get technologies
                        if get_technologies and 'steamdb_results' in results and results['steamdb_results']:
                            steamdb_results_list = results['steamdb_results']
                            status_text.info(f"🔬 Getting technologies for {len(steamdb_results_list)} games...")
                            progress_bar.progress(0.6)
                            
                            tech_count = 0
                            for i, game in enumerate(steamdb_results_list):
                                try:
                                    technologies, status, _ = st.session_state.parser.get_game_technologies(
                                        game['appid'],
                                        game['name']
                                    )
                                    
                                    if technologies:
                                        results['technologies'][game['appid']] = technologies
                                        tech_count += 1
                                    
                                    # Update progress
                                    progress_bar.progress(0.6 + (0.15 * (i + 1) / len(steamdb_results_list)))
                                
                                except Exception as e:
                                    results['technologies'][game['appid']] = [f"Error: {str(e)}"]
                            
                            if tech_count > 0:
                                status_text.success(f"✅ Found technologies for {tech_count} games")
                            else:
                                status_text.info("ℹ️ No technologies found")
                        
                        # Step 4: Find matches
                        if (find_matches and search_psn and search_steamdb and 
                            'psn_results' in results and results['psn_results'] and 
                            'steamdb_results' in results and results['steamdb_results']):
                            
                            psn_results_list = [type('obj', (object,), d)() for d in results['psn_results']]
                            status_text.info(f"🤝 Finding matches between PSN and SteamDB...")
                            progress_bar.progress(0.9)
                            
                            try:
                                matches = st.session_state.parser.find_psn_matches_for_steam_games(
                                    results['steamdb_results'],
                                    max_psn_results=3
                                )
                                
                                # Filter by confidence
                                filtered_matches = {}
                                for game_name, match_data in matches.items():
                                    if match_data.get('match_confidence', 0) >= min_confidence:
                                        filtered_matches[game_name] = match_data
                                
                                results['matches'] = filtered_matches
                                
                                if filtered_matches:
                                    status_text.success(f"✅ Found {len(filtered_matches)} matches with confidence ≥ {min_confidence}")
                                else:
                                    status_text.info(f"ℹ️ No matches found with confidence ≥ {min_confidence}")
                                
                            except Exception as e:
                                status_text.error(f"❌ Match finding failed: {str(e)}")
                                results['matches_error'] = str(e)
                        
                        # Complete
                        progress_bar.progress(1.0)
                        status_text.success("✅ Search completed!")
                        
                        # Store results in session state
                        st.session_state.current_results = results
                        st.session_state.search_history.append({
                            'query': game_query,
                            'time': time.time(),
                            'result_count': len(results.get('psn_results', [])) + len(results.get('steamdb_results', [])),
                            'method': st.session_state.initialization_method,
                            'used_steamdb_cookie': st.session_state.steamdb_cookie_used,
                            'real_traffic': bool(st.session_state.get('last_request_time')),
                            'release_dates_fetched': st.session_state.fetch_release_dates
                        })
                        
                        # Clear progress
                        time.sleep(0.5)
                        progress_container.empty()
                
                finally:
                    # Reset search flag
                    st.session_state.search_in_progress = False
                    st.rerun()
        
        # Display current results if available
        if st.session_state.current_results:
            results = st.session_state.current_results
            
            st.markdown("---")
            st.markdown(f"### 📊 Search Results for '{results['query']}'")
            
            # Show initialization method used
            method_info = []
            if results.get('steamdb_cookie_used'):
                method_info.append("SteamDB Cloudflare Bypass")
                if results.get('custom_user_agent'):
                    method_info.append("Custom User Agent")
                if results.get('real_traffic_simulated'):
                    method_info.append("Real Traffic")
            elif results.get('initialization_method') == 'automatic':
                method_info.append("Automatic")
            
            if results.get('fetch_release_dates'):
                method_info.append("Release Dates")
            
            if method_info:
                st.info(f"**Method used:** {' + '.join(method_info)}")
            
            # Results summary with metrics
            summary_col1, summary_col2, summary_col3, summary_col4, summary_col5 = st.columns(5)
            
            with summary_col1:
                st.metric("SteamDB Results", len(results.get('steamdb_results', [])))
            
            with summary_col2:
                st.metric("PSN Results", len(results.get('psn_results', [])))
            
            with summary_col3:
                st.metric("Matches", len(results.get('matches', [])))
            
            with summary_col4:
                st.metric("Technologies", len(results.get('technologies', {})))
            
            with summary_col5:
                # Count games with release dates
                release_date_count = 0
                for game in results.get('psn_results', []):
                    if game.get('release_date'):
                        release_date_count += 1
                st.metric("Release Dates", release_date_count)
            
            # Display tabs for different result types
            result_tab1, result_tab2, result_tab3, result_tab4 = st.tabs(["🎯 SteamDB Results", "🎮 PSN Results", "🤝 Matches", "🔧 Technologies"])
            
            with result_tab1:
                if results.get('steamdb_results'):
                    for i, game in enumerate(results['steamdb_results']):
                        with st.container():
                            st.markdown('<div class="holographic-card">', unsafe_allow_html=True)
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**{i+1}. {game.get('name', 'Unknown')}**")
                                st.markdown(f"*AppID:* {game.get('appid', 'N/A')}")
                                
                                if game.get('steam_link'):
                                    st.markdown(f"[🔗 Steam Store]({game['steam_link']})")
                                if game.get('steamdb_link'):
                                    st.markdown(f"[📊 SteamDB]({game['steamdb_link']})")
                            
                            with col2:
                                if game.get('image_link'):
                                    try:
                                        st.image(game['image_link'], width=100)
                                    except:
                                        pass
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No SteamDB results to display")
            
            with result_tab2:
                if results.get('psn_results'):
                    for i, game in enumerate(results['psn_results']):
                        with st.container():
                            st.markdown('<div class="holographic-card">', unsafe_allow_html=True)
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**{i+1}. {game.get('name', 'Unknown')}**")
                                
                                # Display platform badges
                                if game.get('platform_tags'):
                                    platform_html = ""
                                    for platform in game['platform_tags']:
                                        platform_lower = platform.lower()
                                        if 'ps4' in platform_lower:
                                            platform_html += '<span class="platform-badge platform-ps4">PS4</span> '
                                        elif 'ps5' in platform_lower:
                                            platform_html += '<span class="platform-badge platform-ps5">PS5</span> '
                                        else:
                                            platform_html += f'<span class="platform-badge platform-multi">{platform}</span> '
                                    
                                    if platform_html:
                                        st.markdown(f"*Platforms:* {platform_html}", unsafe_allow_html=True)
                                
                                st.markdown(f"*Type:* {game.get('game_type', 'Unknown')}")
                                st.markdown(f"*Price:* {game.get('price', 'N/A')}")
                                
                                # Display release date if available
                                if game.get('release_date'):
                                    st.markdown(f"""
                                    <div class="release-date-container">
                                        <span class="release-date-label">Release Date:</span>
                                        <span class="release-date-value">{game['release_date']}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown("*Release Date:* Not available")
                                
                                if game.get('sku_id'):
                                    st.markdown(f"*SKU ID:* `{game['sku_id']}`")
                                
                                if game.get('original_price'):
                                    st.markdown(f"*Original:* ~~{game['original_price']}~~")
                                if game.get('discount_percent'):
                                    st.markdown(f"*Discount:* -{game['discount_percent']}%")
                            
                            with col2:
                                if game.get('url'):
                                    st.markdown(f"[🔗 View on PSN]({game['url']})")
                                if game.get('image_url'):
                                    try:
                                        st.image(game['image_url'], width=100)
                                    except:
                                        pass
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No PSN results to display")
            
            with result_tab3:
                if results.get('matches'):
                    for game_name, match_data in results['matches'].items():
                        with st.container():
                            st.markdown('<div class="holographic-card">', unsafe_allow_html=True)
                            best_match = match_data.get('best_match')
                            confidence = match_data.get('match_confidence', 0)
                            
                            # Confidence color
                            if confidence >= 0.8:
                                conf_color = "🟢"
                            elif confidence >= 0.6:
                                conf_color = "🟡"
                            else:
                                conf_color = "🔴"
                            
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**{game_name}**")
                                st.markdown(f"*Match Confidence:* {conf_color} {confidence:.1%}")
                                
                                if best_match:
                                    st.markdown(f"**PSN Match:** {best_match.get('name', 'Unknown')}")
                                    st.markdown(f"*Type:* {best_match.get('game_type', 'Unknown')}")
                                    st.markdown(f"*Price:* {best_match.get('price', 'N/A')}")
                                    
                                    # Display release date if available
                                    if best_match.get('release_date'):
                                        st.markdown(f"""
                                        <div class="release-date-container">
                                            <span class="release-date-label">Release:</span>
                                            <span class="release-date-value">{best_match['release_date']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    if best_match.get('sku_id'):
                                        st.markdown(f"*SKU ID:* `{best_match['sku_id']}`")
                                    
                                    if best_match.get('url'):
                                        st.markdown(f"[🔗 View on PSN]({best_match['url']})")
                            
                            with col2:
                                if best_match and best_match.get('image_url'):
                                    try:
                                        st.image(best_match['image_url'], width=100)
                                    except:
                                        pass
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No matches to display")
            
            with result_tab4:
                if results.get('technologies'):
                    st.markdown("### 🔧 Technologies & Engines")
                    
                    for appid, tech_list in results['technologies'].items():
                        # Find game name
                        game_name = "Unknown"
                        for game in results.get('steamdb_results', []):
                            if str(game.get('appid')) == str(appid):
                                game_name = game.get('name', 'Unknown')
                                break
                        
                        with st.expander(f"**{game_name}** (AppID: {appid})", expanded=True):
                            st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
                            
                            if not tech_list:
                                st.info("No technologies detected")
                            else:
                                # Categorize technologies
                                engines = []
                                graphics_apis = []
                                sdks = []
                                middleware = []
                                other = []
                                
                                engine_keywords = ['unreal', 'unity', 'source', 'cryengine', 'frostbite', 'creation engine', 'godot', 'gamemaker']
                                graphics_keywords = ['directx', 'vulkan', 'opengl', 'dx11', 'dx12', 'metal']
                                sdk_keywords = ['sdk', 'steamworks', 'epic online services', 'playfab', 'photon']
                                middleware_keywords = ['havok', 'wwise', 'fmod', 'speedtree', 'bink', 'scaleform']
                                
                                for tech in tech_list:
                                    tech_lower = tech.lower()
                                    if any(kw in tech_lower for kw in engine_keywords):
                                        engines.append(tech)
                                    elif any(kw in tech_lower for kw in graphics_keywords):
                                        graphics_apis.append(tech)
                                    elif any(kw in tech_lower for kw in sdk_keywords):
                                        sdks.append(tech)
                                    elif any(kw in tech_lower for kw in middleware_keywords):
                                        middleware.append(tech)
                                    else:
                                        other.append(tech)
                                
                                # Display as compact table
                                st.markdown("""
                                <style>
                                .tech-table {
                                    width: 100%;
                                    border-collapse: collapse;
                                    font-size: 0.85rem;
                                    margin-top: 0.5rem;
                                }
                                .tech-table th {
                                    background: rgba(0, 255, 255, 0.15);
                                    color: #0ff;
                                    text-align: left;
                                    padding: 8px 12px;
                                    font-weight: 600;
                                    border-bottom: 2px solid rgba(0, 255, 255, 0.3);
                                }
                                .tech-table td {
                                    padding: 6px 12px;
                                    border-bottom: 1px solid rgba(0, 255, 255, 0.1);
                                    color: #8af;
                                }
                                .tech-table tr:hover td {
                                    background: rgba(0, 255, 255, 0.05);
                                }
                                .tech-badge {
                                    display: inline-block;
                                    background: rgba(0, 112, 204, 0.3);
                                    border: 1px solid rgba(0, 255, 255, 0.4);
                                    border-radius: 12px;
                                    padding: 2px 8px;
                                    margin: 2px;
                                    font-size: 0.8rem;
                                    color: #0ff;
                                }
                                </style>
                                """, unsafe_allow_html=True)
                                
                                table_html = '<table class="tech-table">'
                                
                                if engines:
                                    table_html += '<tr><th>🎮 Game Engines</th></tr>'
                                    for eng in engines:
                                        table_html += f'<tr><td><span class="tech-badge">{eng}</span></td></tr>'
                                
                                if graphics_apis:
                                    table_html += '<tr><th>🎨 Graphics APIs</th></tr>'
                                    for api in graphics_apis:
                                        table_html += f'<tr><td><span class="tech-badge">{api}</span></td></tr>'
                                
                                if sdks:
                                    table_html += '<tr><th>📦 SDKs & Services</th></tr>'
                                    for sdk in sdks:
                                        table_html += f'<tr><td><span class="tech-badge">{sdk}</span></td></tr>'
                                
                                if middleware:
                                    table_html += '<tr><th>🔧 Middleware</th></tr>'
                                    for mw in middleware:
                                        table_html += f'<tr><td><span class="tech-badge">{mw}</span></td></tr>'
                                
                                if other:
                                    table_html += '<tr><th>🔹 Other Technologies</th></tr>'
                                    for oth in other:
                                        table_html += f'<tr><td><span class="tech-badge">{oth}</span></td></tr>'
                                
                                table_html += '</table>'
                                
                                st.markdown(table_html, unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No technologies to display")
            
            # Export options
            st.markdown("---")
            st.markdown("### 💾 Export Results")
            
            export_col1, export_col2, export_col3 = st.columns(3)
            
            with export_col1:
                if st.button("📥 Download JSON", use_container_width=True):
                    # Create downloadable JSON
                    filename = f"steamdb_psn_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
                    json_str = json.dumps(results, indent=2, ensure_ascii=False)
                    
                    st.download_button(
                        label="Click to download",
                        data=json_str,
                        file_name=filename,
                        mime="application/json",
                        use_container_width=True
                    )
            
            with export_col2:
                if st.button("📋 Copy Summary", use_container_width=True):
                    try:
                        import pyperclip
                        summary_text = f"Search Results for '{results['query']}':\n"
                        summary_text += f"SteamDB Results: {len(results.get('steamdb_results', []))}\n"
                        summary_text += f"PSN Results: {len(results.get('psn_results', []))}\n"
                        summary_text += f"Matches: {len(results.get('matches', []))}\n"
                        summary_text += f"Technologies: {len(results.get('technologies', {}))}\n"
                        
                        # Add release date count
                        release_date_count = 0
                        for game in results.get('psn_results', []):
                            if game.get('release_date'):
                                release_date_count += 1
                        summary_text += f"Release Dates Found: {release_date_count}\n"
                        
                        summary_text += f"Method: {'SteamDB Cookie+UA' if results.get('steamdb_cookie_used') else 'Automatic'}"
                        if results.get('fetch_release_dates'):
                            summary_text += " + Release Dates"
                        
                        pyperclip.copy(summary_text)
                        st.success("✅ Summary copied to clipboard!")
                    except:
                        st.warning("⚠️ Could not copy to clipboard. Pyperclip may not be installed.")
            
            with export_col3:
                if st.button("🗑️ Clear Results", use_container_width=True):
                    st.session_state.current_results = None
                    st.rerun()
    
    with tab2:
        # Technology search
        st.markdown("### 🔧 Search by Technology")
        
        with st.container():
            st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
            tech_col1, tech_col2 = st.columns([3, 1])
            
            with tech_col1:
                tech_query = st.text_input(
                    "Technology name:", 
                    placeholder="e.g., Unity, Unreal Engine, DirectX 11, Vulkan",
                    key="tech_query_input"
                )
            
            with tech_col2:
                tech_max_results = st.number_input(
                    "Max games:", 
                    min_value=1, 
                    max_value=50, 
                    value=15,
                    key="tech_max_results_input"
                )
            
            tech_search_button = st.button(
                "🔬 Search Technology", 
                type="primary", 
                use_container_width=True,
                disabled=st.session_state.search_in_progress or not st.session_state.parser_initialized
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        if tech_search_button:
            if not tech_query:
                st.error("❌ Please enter a technology name.")
            else:
                st.session_state.search_in_progress = True
                
                try:
                    with st.spinner(f"Searching for games using '{tech_query}'..."):
                        tech_results = st.session_state.parser.search_steamdb_for_architecture(tech_query)
                        
                        if tech_results:
                            st.success(f"✅ Found {len(tech_results)} games using '{tech_query}'")
                            
                            # Display results
                            for i, game in enumerate(tech_results[:tech_max_results]):
                                with st.expander(f"{i+1}. {game.get('name', 'Unknown')}"):
                                    st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.markdown(f"**AppID:** `{game.get('appid', 'N/A')}`")
                                        st.markdown(f"**Steam Store:** [🔗 Link]({game.get('steam_link', '#')})")
                                        st.markdown(f"**SteamDB:** [📊 Link]({game.get('steamdb_link', '#')})")
                                        
                                        # Get technologies for this game
                                        tech_button = st.button(
                                            "Get technologies", 
                                            key=f"get_tech_{game.get('appid')}_{i}",
                                            use_container_width=True
                                        )
                                        
                                        if tech_button:
                                            with st.spinner("Getting technologies..."):
                                                technologies, status, _ = st.session_state.parser.get_game_technologies(
                                                    game['appid'],
                                                    game['name']
                                                )
                                                
                                                if technologies:
                                                    st.markdown("**Technologies:**")
                                                    for tech in technologies:
                                                        st.markdown(f"- `{tech}`")
                                                else:
                                                    st.info("No technologies found")
                                    
                                    with col2:
                                        if game.get('image_link'):
                                            try:
                                                st.image(game['image_link'], width=150)
                                            except:
                                                st.info("No image available")
                                    st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.warning(f"ℹ️ No games found using '{tech_query}'")
                
                except Exception as e:
                    st.error(f"❌ Technology search failed: {str(e)}")
                
                finally:
                    st.session_state.search_in_progress = False
    
    with tab3:
        # Batch search
        st.markdown("### 📊 Batch Search")
        
        with st.container():
            st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
            st.info("""
            **Batch Search Features:**
            - Upload a list of game names (one per line)
            - Process multiple games at once
            - Export combined results
            - Compare across games
            - Optional release date fetching
            """)
            
            batch_file = st.file_uploader(
                "Upload game list (txt file):", 
                type=['txt'],
                help="Upload a text file with one game name per line"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        if batch_file:
            games_list = [line.strip() for line in batch_file.read().decode('utf-8').splitlines() if line.strip()]
            st.success(f"✅ Loaded {len(games_list)} games from file")
            
            # Show preview
            with st.expander("Preview games list"):
                st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
                for i, game in enumerate(games_list[:10]):
                    st.write(f"{i+1}. {game}")
                if len(games_list) > 10:
                    st.write(f"... and {len(games_list) - 10} more")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with st.container():
                st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
                batch_options_col1, batch_options_col2 = st.columns(2)
                
                with batch_options_col1:
                    batch_max_results = st.number_input(
                        "Results per game:", 
                        min_value=1, 
                        max_value=20, 
                        value=5,
                        key="batch_max_results"
                    )
                
                with batch_options_col2:
                    batch_delay = st.number_input(
                        "Delay between games (s):", 
                        min_value=0, 
                        max_value=10, 
                        value=2,
                        key="batch_delay"
                    )
                
                # Batch release date option
                batch_fetch_release_dates = st.checkbox(
                    "Fetch release dates for PSN games", 
                    value=st.session_state.get('fetch_release_dates', True),
                    key="batch_fetch_release_dates"
                )
                st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("🔄 Process Batch", type="primary", use_container_width=True,
                        disabled=st.session_state.search_in_progress or not st.session_state.parser_initialized):
                if len(games_list) > 20:
                    st.warning(f"⚠️ Large batch ({len(games_list)} games). This may take a while.")
                    if batch_fetch_release_dates:
                        st.info("📅 Fetching release dates will add extra time (1-2 seconds per game)")
                
                st.session_state.search_in_progress = True
                
                try:
                    # Initialize batch results
                    batch_results = {
                        'games': [],
                        'total_steamdb_results': 0,
                        'total_psn_results': 0,
                        'total_matches': 0,
                        'total_release_dates': 0,
                        'timestamp': time.time(),
                        'initialization_method': st.session_state.initialization_method,
                        'steamdb_cookie_used': st.session_state.steamdb_cookie_used,
                        'custom_user_agent': st.session_state.get('custom_user_agent'),
                        'real_traffic_simulated': bool(st.session_state.get('last_request_time')),
                        'fetch_release_dates': batch_fetch_release_dates
                    }
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, game_name in enumerate(games_list):
                        status_text.info(f"Processing {i+1}/{len(games_list)}: '{game_name}'...")
                        progress_bar.progress((i) / len(games_list))
                        
                        try:
                            # Search SteamDB first
                            steamdb_results = st.session_state.parser.search_steamdb_for_games(
                                game_name,
                                max_results=batch_max_results
                            )
                            
                            # Search PSN with or without release dates
                            if batch_fetch_release_dates:
                                psn_results = st.session_state.parser.search_psn_games_with_release_dates(
                                    game_name, 
                                    max_results=batch_max_results
                                )
                            else:
                                psn_results = st.session_state.parser.psn_scraper.search_games_with_pagination(
                                    game_name, 
                                    max_results=batch_max_results
                                )
                            
                            # Find matches
                            matches = {}
                            if psn_results and steamdb_results:
                                matches = st.session_state.parser.find_psn_matches_for_steam_games(
                                    steamdb_results,
                                    max_psn_results=2
                                )
                            
                            # Count release dates
                            release_date_count = 0
                            for game in psn_results:
                                if hasattr(game, 'release_date') and game.release_date:
                                    release_date_count += 1
                            
                            # Store results
                            game_result = {
                                'name': game_name,
                                'steamdb_results': len(steamdb_results),
                                'psn_results': len(psn_results),
                                'matches': len(matches),
                                'release_dates': release_date_count,
                                'has_best_match': any(match.get('best_match') for match in matches.values())
                            }
                            
                            batch_results['games'].append(game_result)
                            batch_results['total_steamdb_results'] += len(steamdb_results)
                            batch_results['total_psn_results'] += len(psn_results)
                            batch_results['total_matches'] += len(matches)
                            batch_results['total_release_dates'] += release_date_count
                            
                            # Delay between games
                            if i < len(games_list) - 1:
                                time.sleep(batch_delay)
                        
                        except Exception as e:
                            st.error(f"Error processing '{game_name}': {str(e)}")
                            batch_results['games'].append({
                                'name': game_name,
                                'error': str(e)
                            })
                    
                    # Complete
                    progress_bar.progress(1.0)
                    status_text.success(f"✅ Batch processing complete!")
                    
                    # Store batch results
                    st.session_state.batch_results = batch_results
                    
                    # Display batch summary
                    st.markdown("### 📈 Batch Summary")
                    
                    summary_col1, summary_col2, summary_col3, summary_col4, summary_col5 = st.columns(5)
                    
                    with summary_col1:
                        st.metric("Games Processed", len(batch_results['games']))
                    
                    with summary_col2:
                        st.metric("Total SteamDB Results", batch_results['total_steamdb_results'])
                    
                    with summary_col3:
                        st.metric("Total PSN Results", batch_results['total_psn_results'])
                    
                    with summary_col4:
                        st.metric("Total Matches", batch_results['total_matches'])
                    
                    with summary_col5:
                        st.metric("Release Dates", batch_results['total_release_dates'])
                    
                    # Show detailed results
                    with st.expander("View Detailed Results"):
                        st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
                        for game_result in batch_results['games']:
                            if 'error' in game_result:
                                st.markdown(f"**{game_result['name']}** ❌ Error: {game_result['error']}")
                            else:
                                st.markdown(f"**{game_result['name']}**")
                                st.markdown(f"  SteamDB: {game_result['steamdb_results']} | PSN: {game_result['psn_results']} | Matches: {game_result['matches']} | Release Dates: {game_result['release_dates']}")
                                if game_result['has_best_match']:
                                    st.markdown("  ✅ Has best match")
                            
                            st.markdown("---")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Export batch results
                    if st.button("📥 Export Batch Results", use_container_width=True):
                        filename = f"batch_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
                        json_str = json.dumps(batch_results, indent=2, ensure_ascii=False)
                        
                        st.download_button(
                            label="Click to download batch results",
                            data=json_str,
                            file_name=filename,
                            mime="application/json",
                            use_container_width=True
                        )
                
                finally:
                    st.session_state.search_in_progress = False
        
        else:
            st.info("ℹ️ Upload a text file with game names to use batch search.")
            
            # Example file
            st.markdown("**Example file format:**")
            st.code("""Assassin's Creed Valhalla
Cyberpunk 2077
The Witcher 3
Red Dead Redemption 2
Elden Ring
God of War""")
    
    with tab4:
        # Prospero Patches search (PS5)
        st.markdown("### 🎯 PS5 Firmware & Patch Information")
        st.markdown("Search for PS5 game patch history and minimum firmware requirements from Prospero Patches.")
        
        with st.container():
            st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
            
            prospero_col1, prospero_col2 = st.columns([3, 1])
            
            with prospero_col1:
                prospero_query = st.text_input(
                    "Game name:", 
                    placeholder="e.g., Spider-Man Miles Morales, Cyberpunk 2077",
                    key="prospero_query_input"
                )
            
            with prospero_col2:
                prospero_search_button = st.button(
                    "🔍 Search Patches", 
                    use_container_width=True,
                    disabled=not prospero_query
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        if prospero_search_button and prospero_query:
            with st.spinner(f"🔍 Searching for patches: {prospero_query}..."):
                try:
                    # Import the search function
                    from psn_steamdbv2 import search_prospero_patches
                    
                    # Search for patches
                    result = search_prospero_patches(prospero_query)
                    
                    if result.get("success") and result.get("results"):
                        st.success(f"✅ Found {result['total_games']} game(s) with patch data")
                        
                        # Display results for each game
                        for game_data in result["results"]:
                            with st.expander(
                                f"**{game_data['name']}** ({game_data['region']}) - {game_data['patch_count']} patches", 
                                expanded=True
                            ):
                                st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
                                
                                # Header with game info
                                header_col1, header_col2 = st.columns([3, 1])
                                
                                with header_col1:
                                    st.markdown(f"**Title ID:** `{game_data['titleid']}`")
                                    st.markdown(f"**Region:** {game_data['region']}")
                                    
                                    if game_data.get('lowest_firmware'):
                                        st.markdown(f"**Minimum Firmware:** `{game_data['lowest_firmware']}`")
                                    
                                    if game_data.get('latest_version'):
                                        st.markdown(f"**Latest Version:** `{game_data['latest_version']}`")
                                    
                                    if game_data.get('earliest_import'):
                                        st.markdown(f"**First Published:** {game_data['earliest_import']}")
                                    
                                    if game_data.get('last_updated'):
                                        st.markdown(f"**Last Updated:** {game_data['last_updated']}")
                                
                                with header_col2:
                                    if game_data.get('icon'):
                                        try:
                                            st.image(game_data['icon'], width=100)
                                        except:
                                            pass
                                
                                st.markdown("---")
                                st.markdown("### 📋 Patch History")
                                
                                # Display patches in a table-like format
                                patches = game_data.get('patches', [])
                                
                                if patches:
                                    for i, patch in enumerate(patches):
                                        patch_col1, patch_col2, patch_col3, patch_col4 = st.columns([1, 2, 2, 2])
                                        
                                        with patch_col1:
                                            if patch.get('is_latest'):
                                                st.markdown("**✨ Latest**")
                                            else:
                                                st.markdown(f"**#{i+1}**")
                                        
                                        with patch_col2:
                                            st.markdown(f"**Version:** `{patch.get('content_ver', 'N/A')}`")
                                            st.markdown(f"**Size:** {patch.get('filesize', 'N/A')}")
                                        
                                        with patch_col3:
                                            st.markdown(f"**Firmware:** `{patch.get('required_firmware', 'N/A')}`")
                                            st.markdown(f"**Published:** {patch.get('import_date', 'N/A')}")
                                        
                                        with patch_col4:
                                            if patch.get('keyset'):
                                                with st.popover("🔑 Keys"):
                                                    st.code(f"Patch: {patch['keyset'].get('patch', 'N/A')}", language="text")
                                                    st.code(f"Details: {patch['keyset'].get('details', 'N/A')}", language="text")
                                        
                                        if i < len(patches) - 1:
                                            st.markdown("---")
                                else:
                                    st.info("No patch data available")
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Export button
                        st.markdown("---")
                        if st.button("📥 Export Patch Data", use_container_width=True):
                            filename = f"prospero_patches_{prospero_query.replace(' ', '_')}_{time.strftime('%Y%m%d_%H%M%S')}.json"
                            json_str = json.dumps(result, indent=2, ensure_ascii=False)
                            
                            st.download_button(
                                label="Click to download patch data",
                                data=json_str,
                                file_name=filename,
                                mime="application/json",
                                use_container_width=True
                            )
                    
                    elif result.get("error"):
                        st.error(f"❌ Error: {result['error']}")
                    else:
                        st.warning("⚠️ No games found")
                
                except Exception as e:
                    st.error(f"❌ Error searching Prospero Patches: {str(e)}")
                    logger.error(f"Prospero search error: {e}", exc_info=True)
    
    with tab5:
        # Orbis Patches search (PS4)
        st.markdown("### 🕹️ PS4 Patch Information")
        st.markdown("Search for PS4 game patch history and firmware requirements from ORBISPatches.com.")
        
        with st.container():
            st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
            
            orbis_col1, orbis_col2 = st.columns([3, 1])
            
            with orbis_col1:
                orbis_query = st.text_input(
                    "Game name or Title ID:", 
                    placeholder="e.g., Spider-Man, CUSA07408, God of War",
                    key="orbis_query_input"
                )
            
            with orbis_col2:
                orbis_search_button = st.button(
                    "🔍 Search PS4", 
                    use_container_width=True,
                    disabled=not orbis_query
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        if orbis_search_button and orbis_query:
            with st.spinner(f"🔍 Searching ORBISPatches for: {orbis_query}..."):
                try:
                    from psn_steamdbv2 import search_orbis_patches
                    
                    result = search_orbis_patches(orbis_query)
                    
                    if result.get("success") and result.get("results"):
                        st.success(f"✅ Found {result['total_games']} PS4 game(s) with patch data")
                        
                        for game_data in result["results"]:
                            with st.expander(
                                f"**{game_data['name']}** ({game_data.get('region','?')}) — {game_data.get('patch_count', 0)} patches",
                                expanded=True
                            ):
                                st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
                                
                                header_col1, header_col2 = st.columns([3, 1])
                                
                                with header_col1:
                                    st.markdown(f"**Title ID:** `{game_data['titleid']}`")
                                    st.markdown(f"**Region:** {game_data.get('region','N/A')}")
                                    if game_data.get('content_id'):
                                        st.markdown(f"**Content ID:** `{game_data['content_id']}`")
                                    if game_data.get('publisher'):
                                        st.markdown(f"**Publisher:** {game_data['publisher']}")
                                    if game_data.get('lowest_firmware'):
                                        st.markdown(f"**Minimum Firmware:** `{game_data['lowest_firmware']}`")
                                    if game_data.get('latest_version'):
                                        st.markdown(f"**Latest Version:** `{game_data['latest_version']}`")
                                    if game_data.get('last_updated'):
                                        st.markdown(f"**Last Updated:** {game_data['last_updated']}")
                                
                                with header_col2:
                                    if game_data.get('icon'):
                                        try:
                                            st.image(game_data['icon'], width=100)
                                        except:
                                            pass
                                
                                st.markdown("---")
                                st.markdown("### 📋 Patch History")
                                
                                patches = game_data.get('patches', [])
                                
                                if patches:
                                    for i, patch in enumerate(patches):
                                        pc1, pc2, pc3 = st.columns([1, 2, 2])
                                        
                                        with pc1:
                                            if patch.get('is_latest'):
                                                st.markdown('<span class="orbis-latest-badge">✨ Latest</span>', unsafe_allow_html=True)
                                            else:
                                                st.markdown(f"**v{patch.get('version', patch.get('content_ver', 'N/A'))}**")
                                        
                                        with pc2:
                                            st.markdown(f"**Size:** {patch.get('filesize', 'N/A')}")
                                            st.markdown(f"**Firmware:** `{patch.get('required_firmware', 'N/A')}`")
                                        
                                        with pc3:
                                            st.markdown(f"**Date:** {patch.get('creation_date', patch.get('import_date', 'N/A'))}")
                                            if patch.get('changelog_preview'):
                                                with st.popover("📝 Changelog"):
                                                    st.text(patch['changelog_preview'][:500])
                                        
                                        if i < len(patches) - 1:
                                            st.markdown("---")
                                else:
                                    st.info("No patch data available")
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown("---")
                        if st.button("📥 Export PS4 Patch Data", use_container_width=True, key="export_orbis"):
                            filename = f"orbis_patches_{orbis_query.replace(' ', '_')}_{time.strftime('%Y%m%d_%H%M%S')}.json"
                            json_str = json.dumps(result, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="Click to download patch data",
                                data=json_str,
                                file_name=filename,
                                mime="application/json",
                                use_container_width=True,
                                key="dl_orbis"
                            )
                    
                    elif result.get("error"):
                        st.error(f"❌ Error: {result['error']}")
                    else:
                        st.warning("⚠️ No PS4 games found. Try a different name or Title ID (e.g., CUSA12345).")
                
                except ImportError:
                    st.error("❌ `search_orbis_patches` not found in psn_steamdbv2.py. Please add the function (see instructions above).")
                except Exception as e:
                    st.error(f"❌ Error searching ORBISPatches: {str(e)}")
    
    with tab6:
        # Settings tab
        st.markdown("### ⚙️ Application Settings")
        
        with st.container():
            st.markdown('<div class="holographic-container">', unsafe_allow_html=True)
            settings_col1, settings_col2 = st.columns(2)
            
            with settings_col1:
                st.markdown("#### Search Settings")
                
                st.number_input(
                    "Default max results:", 
                    min_value=5, 
                    max_value=100, 
                    value=20,
                    key="default_max_results"
                )
                
                st.number_input(
                    "Request timeout (seconds):", 
                    min_value=10, 
                    max_value=120, 
                    value=30,
                    key="request_timeout"
                )
                
                st.checkbox(
                    "Auto-save results", 
                    value=True,
                    key="auto_save_results"
                )
                
                st.checkbox(
                    "Simulate real traffic for SteamDB", 
                    value=True,
                    key="simulate_real_traffic"
                )
            
            with settings_col2:
                st.markdown("#### Display Settings")
                
                st.checkbox(
                    "Show game images", 
                    value=True,
                    key="show_images"
                )
                
                st.checkbox(
                    "Show confidence scores", 
                    value=True,
                    key="show_confidence"
                )
                
                st.checkbox(
                    "Compact mode", 
                    value=False,
                    key="compact_mode"
                )
                
                st.checkbox(
                    "Show RUM traffic details", 
                    value=True,
                    key="show_rum_details"
                )
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### Data Management")
        
        data_col1, data_col2, data_col3 = st.columns(3)
        
        with data_col1:
            if st.button("🗑️ Clear All Data", use_container_width=True):
                st.session_state.current_results = None
                st.session_state.batch_results = None
                st.session_state.search_history = []
                st.success("All data cleared!")
        
        with data_col2:
            if st.button("📋 View Search History", use_container_width=True):
                if st.session_state.search_history:
                    history_text = "Search History:\n\n"
                    for entry in st.session_state.search_history[-10:]:  # Last 10 entries
                        time_str = time.strftime('%H:%M:%S', time.localtime(entry['time']))
                        method = entry.get('method', 'automatic')
                        cookie = " + SteamDB Cookie" if entry.get('used_steamdb_cookie') else ""
                        traffic = " + Real Traffic" if entry.get('real_traffic') else ""
                        release_dates = " + Release Dates" if entry.get('release_dates_fetched') else ""
                        history_text += f"{time_str}: '{entry['query']}' - {entry['result_count']} results ({method}{cookie}{traffic}{release_dates})\n"
                    
                    st.text_area("Recent Searches:", history_text, height=150)
                else:
                    st.info("No search history available")
        
        with data_col3:
            if st.button("🔄 Reset Settings", use_container_width=True):
                for key in ['default_max_results', 'request_timeout', 'auto_save_results', 
                           'show_images', 'show_confidence', 'compact_mode', 
                           'simulate_real_traffic', 'show_rum_details']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Settings reset to defaults!")

# Debug information (if enabled)
if st.session_state.get('show_debug', False):
    st.markdown("---")
    st.markdown("### 🔍 Debug Information")
    
    with st.expander("Session State"):
        debug_data = {}
        for key, value in st.session_state.items():
            if key == 'parser' and value is not None:
                debug_data[key] = f"<SteamDBSeleniumParser at {hex(id(value))}>"
            elif key == 'cf_clearance_cookie' and value is not None:
                # Mask cookie value and User Agent for security
                masked_cookie = {k: ('***MASKED***' if k == 'value' else v) for k, v in value.items()}
                if 'user_agent' in masked_cookie and masked_cookie['user_agent']:
                    masked_cookie['user_agent'] = masked_cookie['user_agent'][:50] + "..."
                debug_data[key] = masked_cookie
            elif key == 'custom_user_agent' and value is not None:
                debug_data[key] = value[:50] + "..." if len(value) > 50 else value
            elif key == 'steamdb_headers' and value is not None:
                debug_data[key] = {k: (v[:50] + "..." if len(str(v)) > 50 else v) for k, v in value.items()}
            elif isinstance(value, (list, dict)) and len(str(value)) > 100:
                debug_data[key] = f"{type(value).__name__} with {len(value)} items"
            else:
                debug_data[key] = value
        
        st.json(debug_data)
    
    with st.expander("System Information"):
        import platform
        sys_info = {
            "Python Version": sys.version,
            "Streamlit Version": st.__version__,
            "Platform": platform.platform(),
            "Processor": platform.processor(),
            "System": platform.system(),
            "Machine": platform.machine()
        }
        st.json(sys_info)
    
    with st.expander("Real Traffic Simulation Info"):
        if st.session_state.get('last_request_time'):
            time_since = time.time() - st.session_state.last_request_time
            st.markdown(f"**Last RUM request:** {time_since:.1f} seconds ago")
        
        if st.session_state.get('steamdb_headers'):
            st.markdown("**Current SteamDB headers configured:**")
            st.json({k: (v[:80] + "..." if len(str(v)) > 80 else v) for k, v in st.session_state.steamdb_headers.items()})
    
    with st.expander("Release Date Extraction Info"):
        st.markdown("""
        **Release Date Extraction Features:**
        - Multiple language support (FI, EN, DE, FR, JP, etc.)
        - Multiple parsing strategies
        - Responsive layout handling
        - Regular expression fallback
        
        **Languages Supported:**
        - Finnish: "Julkaisu:"
        - English: "Release Date:"
        - German: "Veröffentlichungsdatum:"
        - Spanish: "Fecha de lanzamiento:"
        - Italian: "Data di pubblicazione:"
        - Japanese: "発売日:"
        - Russian: "Дата выхода:"
        - Korean: "출시일:"
        - Arabic: "تاريخ الإصدار:"
        """)

# Footer with enhanced status display
st.markdown("---")

# Status information box with size constraints
st.markdown("""
<div style="max-width: 100%; background: rgba(17, 17, 17, 0.95); border: 1px solid rgba(0, 255, 255, 0.3); 
            border-radius: 15px; padding: 1.5rem; margin-bottom: 1rem; overflow: hidden;">
    <div style="color: #0ff; font-size: 1.2rem; margin-bottom: 1rem; text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);">
        ✅ Parser Ready!
    </div>
    <div style="max-width: 100%; color: #8af; font-size: 0.9rem; line-height: 1.6;">
        <div style="margin-bottom: 0.5rem; max-width: 800px; word-wrap: break-word;">• <strong>Initialization:</strong> SteamDB Bypass (Cookie+UA)</div>
        <div style="margin-bottom: 0.5rem; max-width: 800px;">• <strong>Headless Mode:</strong> ✅ Enabled</div>
        <div style="margin-bottom: 0.5rem; max-width: 800px;">• <strong>PSN Region:</strong> fi-fi</div>
        <div style="margin-bottom: 0.5rem; max-width: 800px;">• <strong>Release Dates:</strong> ✅ Enabled</div>
        <div style="margin-bottom: 0.5rem; max-width: 800px;">• <strong>Status:</strong> Ready for search operations</div>
    </div>
</div>
""", unsafe_allow_html=True)

# User Agent display with size constraint
if st.session_state.get('custom_user_agent'):
    ua_display = st.session_state.custom_user_agent
    if len(ua_display) > 100:
        ua_display = ua_display[:97] + "..."
    
    st.markdown(f"""
<div style="max-width: 100%; background: rgba(17, 17, 17, 0.95); border: 1px solid rgba(0, 255, 255, 0.3); 
            border-radius: 15px; padding: 1rem; margin-bottom: 1rem; overflow: hidden;">
    <div style="color: #0ff; font-size: 1rem; margin-bottom: 0.5rem;">🔧 Current User Agent</div>
    <div style="max-width: 100%; color: #8af; font-size: 0.85rem; word-break: break-all; overflow-wrap: break-word;">
        {ua_display}
    </div>
</div>
""", unsafe_allow_html=True)

# SteamDB Headers status
if st.session_state.get('steamdb_headers'):
    time_since_last = ""
    if st.session_state.get('last_request_time'):
        time_diff = int(time.time() - st.session_state.last_request_time)
        time_since_last = f"🔄 Last real traffic simulation: {time_diff}s ago"
    
    st.markdown(f"""
<div style="max-width: 100%; background: rgba(17, 17, 17, 0.95); border: 1px solid rgba(0, 255, 255, 0.3); 
            border-radius: 15px; padding: 1rem; margin-bottom: 1rem; overflow: hidden;">
    <div style="color: #0ff; font-size: 1rem; margin-bottom: 0.5rem;">📋 SteamDB Headers Configured</div>
    <div style="color: #8af; font-size: 0.85rem; max-width: 800px;">{time_since_last}</div>
</div>
""", unsafe_allow_html=True)

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("**Version:** 2.6.0 (Prospero + Enhanced Status)")

with footer_col2:
    status = "✅ Ready" if st.session_state.parser_initialized else "❌ Not Initialized"
    if st.session_state.parser_initialized:
        method = "SteamDB Cookie" if st.session_state.steamdb_cookie_used else "Auto"
        release_dates = " + Release Dates" if st.session_state.fetch_release_dates else ""
        status += f" ({method}{release_dates})"
    st.markdown(f"**Status:** {status}")

with footer_col3:
    st.markdown(f"**Last Updated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Add a refresh button at the bottom
if st.button("🔄 Refresh Page", use_container_width=True):
    st.rerun()