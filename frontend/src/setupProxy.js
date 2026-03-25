const { createProxyMiddleware } = require('http-proxy-middleware');

const CRAWLER_AGENTS = /facebookexternalhit|twitterbot|whatsapp|telegrambot|linkedinbot|slackbot|discordbot|pinterest|googlebot|bingbot|yandexbot|applebot|snapchat/i;

module.exports = function(app) {
  // Intercept /plano/{slug} for social crawlers → serve pre-rendered HTML from backend
  app.use('/plano', (req, res, next) => {
    const ua = req.headers['user-agent'] || '';
    if (CRAWLER_AGENTS.test(ua)) {
      // Extract slug from path
      const slug = req.path.replace(/^\//, '');
      if (slug) {
        return res.redirect(307, `/api/ssr/plano/${slug}`);
      }
    }
    next();
  });
};
