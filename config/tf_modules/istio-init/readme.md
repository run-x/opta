# What is this module?
This is the module for a simple istio setup in opta.

# How does it work?
It works by installing the istio operator, and then a simple profile for it
to enact, as described [here](https://istio.io/latest/docs/setup/install/operator/).

# What's the istio-operator?
Think of it as the babysitter for the istio installation that helps with the setup
and preservation. A lot of it is what the `istioctl install` does and this
was the only other option except the 4-part "raw" new (direct support for helm was previously dropped in v 1.6) helm 
installation which is in alpha.

# So... just pay attention to the "profile" part?
Yup, the operator works in the shadows.