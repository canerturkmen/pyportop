from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pyportop.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

#    url(r'^admin/', include(admin.site.urls)),
    url(r'^optimize/', 'interface.views.optimize', name="optimize"),
    url(r'^backtest/', 'interface.views.backtest', name="backtest"),
)
