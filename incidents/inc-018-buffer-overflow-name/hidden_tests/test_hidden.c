#include "badge.h"
#include "harness.h"

TEST(normal_name_prints_unchanged) {
    badge_t *b = badge_create(10, "Attendee", "Priya Nair");
    char line[128];
    badge_format(b, line, sizeof(line));
    CHECK_EQ_STR(line, "Priya Nair (Attendee) #0010");
    badge_free(b);
}

TEST(oversized_roster_name_is_truncated_not_overflowed) {
    /* Well past BADGE_NAME_LEN (32) - the kind of value a vendor's roster
     * upload actually contains once two names get pasted into one field. */
    const char *raw = "Alexandra Bartholomew Christopherson Worthington";
    CHECK(strlen(raw) > BADGE_NAME_LEN);

    badge_t *b = badge_create(4021, "Attendee", raw);
    CHECK(strlen(b->name) == BADGE_NAME_LEN - 1);
    CHECK(strncmp(b->name, raw, BADGE_NAME_LEN - 1) == 0);

    char line[128];
    badge_format(b, line, sizeof(line));
    CHECK(strstr(line, "#4021") != NULL);

    badge_free(b);
}

int main(void) {
    return RUN_ALL();
}
