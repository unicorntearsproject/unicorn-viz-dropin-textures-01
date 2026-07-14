Owner: unicorn-viz
Status: current
Last updated: 2026-07-13

# Texture provenance

The `nebula_*`, `galaxy_*`, `star_cluster_*`, `saturn_rings`, `jupiter_storms`,
and `solar_flare` images in this directory are sourced from the
[NASA Image and Video Library](https://images.nasa.gov/) via its public
`images-api.nasa.gov` REST API. All NASA imagery is public domain (CC0 1.0
Universal) per NASA's media usage guidelines — free to use, modify, and
redistribute with no attribution required.

| File | NASA ID |
|------|---------|
| nebula_eagle.jpg | PIA25433 |
| nebula_horsehead.jpg | GSFC_20171208_Archive_e001518 |
| nebula_lagoon.jpg | GSFC_20171208_Archive_e001955 |
| nebula_ring.jpg | GSFC_20171208_Archive_e001464 |
| nebula_orion_infrared.jpg | PIA25434 |
| galaxy_spiral_burst.jpg | GSFC_20171208_Archive_e000877 |
| galaxy_spiral_classic.jpg | GSFC_20171208_Archive_e000158 |
| solar_flare.jpg | PIA21958 |
| saturn_rings.jpg | PIA02241 |
| jupiter_storms.jpg | PIA01262 |
| star_cluster_globular.jpg | GSFC_20171208_Archive_e000191 |
| star_cluster_young.jpg | GSFC_20171208_Archive_e001789 |

Re-fetch any of these directly: `https://images-api.nasa.gov/asset/<NASA ID>`
returns a manifest of available sizes; the `~large.jpg` variant was used here.

All other files in this directory (`checker_*`, `dots_*`, `waves_*`, etc.) are
procedurally generated, not sourced from the internet.
