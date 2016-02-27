# QGis bivariate legend


## Purpose

This plugin enables generation of legend for bivariate analysis.

You can see it in action with this below screencast.

![Bivariate legend demo](qgis-bivariate-legend-v0.1.gif)

We only manage colors, no patterns. It may change but is not intended at the moment.

## Warning

It's an early version. We plan to manage below issues:

* manage borders colors. We encountered some issues in our tests
* catch every uses cases the plugin was not intended for, in particular related to "right" `rendererv2` types.
* manage `"Rule-based"` analysis (hence, only use `"Graduated"` or `"categorized"` analysis)
* i18n support with translation

## Installation

You just need to install it by downloading the zip file or by adding the plugin.xml URL as an external plugin through the plugin manager.

## Contact us

You can open an issue on [the repository] or drop us an email at
contact(at)webgeodatavore.com

Feel free to submit a PR (Pull Request) if you feel it can improve the plugin overall functions.
