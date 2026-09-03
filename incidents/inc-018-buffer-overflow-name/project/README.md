# Badge printer

Formats attendee badges from the conference roster upload: id, title, and a
name field that comes straight from whatever a vendor typed into a CSV.

    cc -fsanitize=address,undefined -g -Isrc -o build/app src/*.c
    ./build/app                    # prints the badge for data/roster.txt
    cc -fsanitize=address,undefined -g -Isrc -Itests -o build/tests src/badge.c tests/test_badge.c
    ./build/tests

`badge_create(id, title, name)` allocates a `badge_t` and copies `title` and
`name` into its fixed-size fields. `badge_format()` writes the printable
line into a caller-supplied buffer. `badge_free()` releases it.
