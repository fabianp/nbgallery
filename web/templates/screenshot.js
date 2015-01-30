
var page = require('webpage').create();
var redirectURL = null;
 

page.viewportSize = {
  width: 800,
  height: 800
};
page.clipRect = {
  top: 0,
  left: 30,
  width: 800,
  height: 800
};
page.settings.resourceTimeout = 5000; // 5 seconds

page.onResourceError = function(resourceError) {
    page.reason = resourceError.errorString;
    page.reason_url = resourceError.url;
};


page.open('%s', function(status) {
  console.log(status);
  page.evaluate(function () {
    jQuery('.navbar').remove()
    jQuery('.breadcrumbs').remove();
  })
  page.render('%s'); 
  phantom.exit();
});