/**
 * Vitis-AI Backend Server
 * Основной сервер Node.js для системы оценки пригодности земель для виноделия
 * 
 * Функционал:
 * - REST API для оценки участков
 * - Аутентификация и авторизация (JWT)
 * - Интеграция с MongoDB для хранения GeoJSON данных
 * - Кэширование запросов к внешним API
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const dotenv = require('dotenv');
const mongoose = require('mongoose');

// Load environment variables
dotenv.config();

// Import routes
const authRoutes = require('./routes/auth');
const evaluationRoutes = require('./routes/evaluation');
const userRoutes = require('./routes/users');

// Import middleware
const { errorHandler } = require('./middleware/errorHandler');
const { authenticateToken } = require('./middleware/auth');

const app = express();
const PORT = process.env.PORT || 3000;

// ============================================
// Security & Middleware
// ============================================

// Helmet for security headers
app.use(helmet());

// CORS configuration
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:8501', // Streamlit default port
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

app.use('/api/', limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging
if (process.env.NODE_ENV === 'development') {
  app.use(morgan('dev'));
}

// ============================================
// Database Connection
// ============================================

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/vitis-ai');
    console.log(`✅ MongoDB Connected: ${conn.connection.host}`);
    
    // Create indexes for geospatial queries
    const Evaluation = require('./models/Evaluation');
    await Evaluation.createIndexes();
    console.log('✅ Database indexes created');
  } catch (error) {
    console.error('❌ MongoDB Connection Error:', error.message);
    process.exit(1);
  }
};

// ============================================
// Routes
// ============================================

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    service: 'Vitis-AI Backend',
    version: '1.0.0'
  });
});

// Public routes
app.get('/', (req, res) => {
  res.json({
    name: 'Vitis-AI API',
    description: 'Система оценки пригодности земель для виноделия',
    version: '1.0.0',
    endpoints: {
      health: 'GET /health',
      auth: 'POST /api/auth/register, POST /api/auth/login',
      evaluate: 'POST /api/evaluate',
      history: 'GET /api/user/history',
      admin: 'GET /api/admin/stats'
    }
  });
});

// Authentication routes (public)
app.use('/api/auth', authRoutes);

// Protected routes
app.use('/api/evaluate', authenticateToken, evaluationRoutes);
app.use('/api/user', authenticateToken, userRoutes);

// Admin routes (requires admin role)
// app.use('/api/admin', authenticateToken, requireAdmin, adminRoutes);

// ============================================
// Error Handling
// ============================================

// 404 handler
app.use((req, res, next) => {
  res.status(404).json({
    success: false,
    message: 'Endpoint not found'
  });
});

// Global error handler
app.use(errorHandler);

// ============================================
// Server Start
// ============================================

const startServer = async () => {
  try {
    // Connect to database
    await connectDB();
    
    // Start server
    app.listen(PORT, () => {
      console.log(`\n🚀 Vitis-AI Backend Server started`);
      console.log(`📍 Port: ${PORT}`);
      console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
      console.log(`🔗 API URL: http://localhost:${PORT}`);
      console.log(`📊 Health Check: http://localhost:${PORT}/health\n`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

// Handle unhandled promise rejections
process.on('unhandledRejection', (err) => {
  console.error('❌ Unhandled Rejection:', err);
  server.close(() => process.exit(1));
});

// Handle SIGTERM
process.on('SIGTERM', () => {
  console.log('👋 SIGTERM received. Shutting down gracefully...');
  process.exit(0);
});

startServer();

module.exports = app;
