// Service worker for push notifications
self.addEventListener('push', function(event){
  var data = { title: 'RamsTech', body: 'New update', url: '/' };
  try{
    data = Object.assign(data, event.data.json());
  } catch(e){}

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon-192.svg',
      badge: '/icon-192.svg',
      tag: 'ramstech-' + Date.now(),
      data: { url: data.url }
    })
  );
});

self.addEventListener('notificationclick', function(event){
  event.notification.close();
  var url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(list){
      for(var i=0; i<list.length; i++){
        if(list[i].url.indexOf(self.location.origin) === 0){
          return list[i].focus();
        }
      }
      if(clients.openWindow) return clients.openWindow(url);
    })
  );
});
