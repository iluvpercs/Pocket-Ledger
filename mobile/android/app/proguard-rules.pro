# Dart/Drift code is compiled ahead of time and is not affected by R8. These
# rules keep the Java-side SQLite FFI entry points intact when minification is
# enabled for release builds.
-keep class sqlite3.** { *; }
-keep class com.sqlite3.** { *; }
-keep class org.sqlite.** { *; }
