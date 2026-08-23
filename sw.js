// ===============================================
// Service Worker — وَذَكِّر
// Network-First لصفحة التطبيق (لضمان وصول آخر تحديث فورًا)
// Cache-First للأيقونات والخطوط (أداء أسرع + عمل بدون إنترنت)
// + دمج OneSignal لإشعارات Push حقيقية تصل حتى لو التطبيق مقفول تمامًا
// ===============================================
// نحيط الاستيراد بـ try/catch: لو فشل تحميل سكريبت OneSignal مؤقتًا (مشكلة شبكة
// عابرة مثلاً)، لا نريد أن يتوقف منطق الكاش/التحديث الخاص بنا تبعًا لذلك.
try{
  importScripts('https://cdn.onesignal.com/sdks/web/v16/OneSignalSDKWorker.js');
}catch(e){
  console.error('[sw.js] فشل تحميل OneSignal Worker:', e);
}

const CACHE_NAME = 'wazakkir-v2.10.0';
const STATIC_ASSETS = [
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/favicon.png',
  'quran.json',
  'tafsir.json',
  'https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Tajawal:wght@300;400;500;700;900&display=swap'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS).catch(()=>{}))
  );
  // NOTE: intentionally NOT calling self.skipWaiting() here.
  // The new worker stays in "waiting" state until the user taps
  // "تحديث الآن" (Update banner), which posts SKIP_WAITING to it.
  // This is what makes the update-available banner possible.
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Allow page to force-activate a waiting worker immediately
self.addEventListener('message', event => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = event.request.url;
  const isHTML = event.request.mode === 'navigate' || url.endsWith('.html') || url.endsWith('/');
  const isManifest = url.endsWith('manifest.json');

  if (isHTML || isManifest) {
    // Network-first: always try to get the freshest version first
    event.respondWith(
      fetch(event.request).then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => caches.match(event.request).then(c => c || caches.match('index.html')))
    );
    return;
  }

  // Cache-first for static assets (icons, fonts, etc.)
  event.respondWith(
    caches.match(event.request).then(cached => {
      return cached || fetch(event.request).then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => cached);
    })
  );
});

// ملاحظة: معالجة الإشعارات (push / notificationclick) بقت بالكامل تحت
// إدارة مكتبة OneSignal المستوردة أعلاه عبر importScripts — لذلك تم حذف
// أي معالجات push/notificationclick مخصصة هنا لتفادي أي تعارض أو ازدواج
// في عرض الإشعارات.
