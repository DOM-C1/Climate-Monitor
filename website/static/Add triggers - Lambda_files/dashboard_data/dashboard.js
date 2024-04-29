function onHashChange(dashboardName) {
    let hash = window.location.hash;
    if (/dashboards:name/.test(hash)) {
        const pair = hash.split('=');
        if (pair.length === 2) {
            CloudWatchDashboards.load(pair[1]);
        }
    } else if (/#dashboards\/dashboard/.test(hash)) {
        dashboardName = '';
        if (hash.includes('?')) {
            hash = hash.split('?')[0];
        }
        let splittedPath = hash.split('/');
        if (splittedPath.length > 2) {
            dashboardName = splittedPath[2];
        }
        CloudWatchDashboards.load(dashboardName);
    }
    else if (typeof dashboardName != 'string' ) {
        // In case where dashboardName is event. Happens because this function is listening to hashchange event.
        CloudWatchDashboards.load('');
    } else {
        CloudWatchDashboards.load(dashboardName || '');
    }
}

function receiveMessage(event) {
    CloudWatchDashboards.executeMessage(event.data, event.origin);
}

function parseVariables() {
    var query = window.location.search.substring(1);
    var vars = query.split('&');

    return vars.reduce(function(agg, variable) {
        var pair = variable.split('=');
        agg[pair[0]] = pair[1];

        return agg;
    }, {});
}

function parseConfig(encodedStringifiedConfig) {
    try {
        var stringifiedConfig = decodeURIComponent(encodedStringifiedConfig);
        return JSON.parse(stringifiedConfig);
    } catch (e) {
        // Could not parse config, swallow exception & return empty object
        return {};
    }
}

(function pageLoaded() {
    var params = parseVariables(),
        dashboardContainerEl = document.getElementById('cwdb-container'),
        accountId = params['accountId'],
        config = parseConfig(params['config']),
        dashboardName = params['name'],
        // as params['origin] can contain a URL, it can end up being URL encoded when e.g redirected from signin
        topOrigin = decodeURIComponent(params['origin'] || this.top.location.origin),
        parsedConfig,
        isCustomDashboard;

    if (this.CloudWatchDashboards) {
        if (accountId) {
            CloudWatchDashboards.setAccountId(accountId);
        }
        if ((this.top.location !== this.location) && this.parent) {
            // TODO phase out isPolaris argument
            parsedConfig = CloudWatchDashboards.initEmbeddedMode(this.parent, topOrigin, undefined, config);
        }

        isCustomDashboard = parsedConfig && parsedConfig.displayMode === 'static';
        CloudWatchDashboards.initDashboard(dashboardContainerEl, true, isCustomDashboard);
        onHashChange(dashboardName);
        this.addEventListener('message', receiveMessage, false);
        this.addEventListener('hashchange', onHashChange, false);
    }
})();
