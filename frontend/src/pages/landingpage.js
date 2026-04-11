import React from 'react';
import { useNavigate } from 'react-router-dom';

const styles = {
    page: {
        minHeight: '100vh',
        backgroundColor: '#f5f4ed', // Parchment
        color: '#141413', // Anthropic Near Black
        fontFamily: "system-ui, -apple-system, sans-serif",
        overflowX: 'hidden',
    },
    nav: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '24px 48px',
        borderBottom: '1px solid #f0eee6', // Border Cream
        backgroundColor: '#faf9f5', // Ivory
    },
    logo: {
        fontFamily: "'Georgia', serif",
        fontSize: '24px',
        fontWeight: 500,
        color: '#141413',
        letterSpacing: '-0.02em',
    },
    btnSecondary: {
        backgroundColor: '#e8e6dc', // Warm Sand
        color: '#4d4c48', // Charcoal Warm
        padding: '8px 16px',
        borderRadius: '8px',
        border: 'none',
        fontSize: '15px',
        fontWeight: 500,
        cursor: 'pointer',
        boxShadow: '0px 0px 0px 1px #d1cfc5', // Ring Warm
        transition: 'background 0.2s',
    },
    btnPrimary: {
        backgroundColor: '#c96442', // Terracotta Brand
        color: '#faf9f5', // Ivory
        padding: '12px 24px',
        borderRadius: '12px',
        border: 'none',
        fontSize: '16px',
        fontWeight: 500,
        cursor: 'pointer',
        boxShadow: '0px 0px 0px 1px #c96442',
        transition: 'opacity 0.2s',
    },
    hero: {
        maxWidth: '800px',
        margin: '120px auto 160px auto',
        textAlign: 'center',
        padding: '0 24px',
    },
    headline: {
        fontFamily: "'Georgia', serif",
        fontSize: '64px',
        fontWeight: 500,
        lineHeight: 1.10,
        color: '#141413',
        marginBottom: '24px',
    },
    subheadline: {
        fontFamily: "system-ui, sans-serif",
        fontSize: '20px',
        lineHeight: 1.60,
        color: '#5e5d59', // Olive Gray
        maxWidth: '600px',
        margin: '0 auto 40px auto',
    },
    featureSection: {
        backgroundColor: '#141413', // Near Black Section
        padding: '120px 48px',
        color: '#f5f4ed',
    },
    featureGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '32px',
        maxWidth: '1200px',
        margin: '0 auto',
    },
    cardDark: {
        backgroundColor: '#30302e', // Dark Surface
        border: '1px solid #30302e',
        borderRadius: '12px',
        padding: '40px 32px',
    },
    cardTitle: {
        fontFamily: "'Georgia', serif",
        fontSize: '25px',
        fontWeight: 500,
        color: '#faf9f5',
        marginBottom: '16px',
        lineHeight: 1.20,
    },
    cardDesc: {
        fontFamily: "system-ui, sans-serif",
        fontSize: '16px',
        lineHeight: 1.60,
        color: '#b0aea5', // Warm Silver
    }
};

export default function LandingPage() {
    const navigate = useNavigate();

    return (
        <div style={styles.page}>
            <nav style={styles.nav}>
                <div style={styles.logo}>Unitwise</div>
                <button
                    style={styles.btnSecondary}
                    onClick={() => navigate('/login')}
                    onMouseEnter={(e) => e.target.style.backgroundColor = '#d1cfc5'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = '#e8e6dc'}
                >
                    Sign In
                </button>
            </nav>

            <main style={styles.hero}>
                <h1 style={styles.headline}>Your syllabus, beautifully understood.</h1>
                <p style={styles.subheadline}>
                    A thoughtful academic companion designed for your university curriculum. Stop parsing through hundreds of pages of unread PDFs. Ask a question, and get a structured, exam-ready answer.
                </p>
                <button
                    style={styles.btnPrimary}
                    onClick={() => navigate('/login')}
                    onMouseEnter={(e) => e.target.style.opacity = 0.9}
                    onMouseLeave={(e) => e.target.style.opacity = 1}
                >
                    Start Studying
                </button>
            </main>

            <section style={styles.featureSection}>
                <div style={styles.featureGrid}>
                    <div style={styles.cardDark}>
                        <h3 style={styles.cardTitle}>Syllabus-Sourced</h3>
                        <p style={styles.cardDesc}>We do not guess or hallucinate. Every answer is carefully extracted from your specific textbook and lecture notes.</p>
                    </div>
                    <div style={styles.cardDark}>
                        <h3 style={styles.cardTitle}>Exam-Centric Clarity</h3>
                        <p style={styles.cardDesc}>Answers are formatted precisely how you need to write them—clear headings, structured bullet points, and high-signal information.</p>
                    </div>
                    <div style={styles.cardDark}>
                        <h3 style={styles.cardTitle}>Uninterrupted Focus</h3>
                        <p style={styles.cardDesc}>A calm, distraction-free environment designed to feel like reading a good book rather than browsing a digital dashboard.</p>
                    </div>
                </div>
            </section>
        </div>
    );
}