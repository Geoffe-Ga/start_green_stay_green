// Tizen native watch-app entry point for wrist-pulse.
//
// NOTE: this file needs the Tizen native SDK headers (watch_app.h, EFL)
// and is built by Tizen Studio, NOT by the plain CMake build — see
// CMakeLists.txt and the README for the build split.
#include <watch_app.h>
#include <watch_app_efl.h>
#include <Elementary.h>

#include <cstdio>

#include "greeting.h"

namespace {

struct appdata_s {
    Evas_Object *win = nullptr;
    Evas_Object *conform = nullptr;
    Evas_Object *label = nullptr;
};

// Renders the greeting and the current time onto the watch face label.
void update_watch_label(appdata_s *ad, watch_time_h watch_time) {
    if (ad->label == nullptr || watch_time == nullptr) {
        return;
    }

    int hour24 = 0;
    int minute = 0;
    watch_time_get_hour24(watch_time, &hour24);
    watch_time_get_minute(watch_time, &minute);

    const std::string greeting =
        wrist_pulse::format_greeting("wrist-pulse");
    char text[256];
    std::snprintf(text, sizeof(text),
                  "<align=center>%s<br/>%02d:%02d</align>",
                  greeting.c_str(), hour24, minute);
    elm_object_text_set(ad->label, text);
}

// Builds the base EFL UI: window, conformant, and the greeting label.
void create_base_gui(appdata_s *ad, int width, int height) {
    watch_app_get_elm_win(&ad->win);
    evas_object_resize(ad->win, width, height);

    ad->conform = elm_conformant_add(ad->win);
    evas_object_size_hint_weight_set(ad->conform, EVAS_HINT_EXPAND,
                                     EVAS_HINT_EXPAND);
    elm_win_resize_object_add(ad->win, ad->conform);
    evas_object_show(ad->conform);

    ad->label = elm_label_add(ad->conform);
    evas_object_resize(ad->label, width, height / 3);
    evas_object_move(ad->label, 0, height / 3);
    evas_object_show(ad->label);

    evas_object_show(ad->win);
}

bool app_create(int width, int height, void *data) {
    auto *ad = static_cast<appdata_s *>(data);
    create_base_gui(ad, width, height);
    return true;
}

void app_terminate(void * /*data*/) {
    // Release any resources acquired in app_create here.
}

void app_time_tick(watch_time_h watch_time, void *data) {
    auto *ad = static_cast<appdata_s *>(data);
    update_watch_label(ad, watch_time);
}

}  // namespace

int main(int argc, char *argv[]) {
    appdata_s ad;
    watch_app_lifecycle_callback_s callbacks = {};
    callbacks.create = app_create;
    callbacks.terminate = app_terminate;
    callbacks.time_tick = app_time_tick;

    return watch_app_main(argc, argv, &callbacks, &ad);
}
