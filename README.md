# packages.seqan.de
Scripts for building and publishing http://packages.seqan.de

## Automatic deployment

The script `deploy_finalize.sh` scans the target directory (containing seqan3-library-* archives) and removes all but
the most recent nightly stable archives. It then rebuilds the html site for packages.seqan.de.
