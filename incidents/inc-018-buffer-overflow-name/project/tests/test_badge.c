#include "badge.h"
#include "harness.h"

TEST(create_formats_a_normal_name) {
    badge_t *b = badge_create(1001, "Speaker", "Jordan Lee");
    char line[128];
    badge_format(b, line, sizeof(line));
    CHECK_EQ_STR(line, "Jordan Lee (Speaker) #1001");
    badge_free(b);
}

TEST(title_longer_than_field_is_truncated) {
    badge_t *b = badge_create(2, "Volunteer Coordinator", "Sam Ortiz");
    CHECK(strlen(b->title) < BADGE_TITLE_LEN);
    badge_free(b);
}

TEST(id_is_zero_padded) {
    badge_t *b = badge_create(7, "Staff", "Ana Reyes");
    char line[128];
    badge_format(b, line, sizeof(line));
    CHECK(strstr(line, "#0007") != NULL);
    badge_free(b);
}

TEST(short_names_round_trip) {
    badge_t *b = badge_create(42, "Attendee", "Kim");
    CHECK_EQ_STR(b->name, "Kim");
    badge_free(b);
}

int main(void) {
    return RUN_ALL();
}
