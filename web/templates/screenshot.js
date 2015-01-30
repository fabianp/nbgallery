var resourceWait  = 300,
    maxRenderWait = 10000,
    url           = '%s';

var page          = require('webpage').create(),
    count         = 0,
    forcedRenderTimeout,
    renderTimeout;

page.viewportSize = { width: 800, height : 800 };

page.clipRect = {
  top: 0,
  left: 30,
  width: 800,
  height: 800
};

function doRender() {
   page.evaluate(function () {
     jQuery('.navbar').remove()
     jQuery('.breadcrumb').remove();
  })
    page.render('%s');
    phantom.exit();
}

page.onResourceRequested = function (req) {
    count += 1;
    console.log('> ' + req.id + ' - ' + req.url);
    clearTimeout(renderTimeout);
};

page.onResourceReceived = function (res) {
    if (!res.stage || res.stage === 'end') {
        count -= 1;
        console.log(res.id + ' ' + res.status + ' - ' + res.url);
        if (count === 0) {
            renderTimeout = setTimeout(doRender, resourceWait);
        }
    }
};

page.open(url, function (status) {
    if (status !== "success") {
        console.log('Unable to load url');
        phantom.exit();
    } else {
        forcedRenderTimeout = setTimeout(function () {
            console.log(count);
            doRender();
        }, maxRenderWait);
    }
});