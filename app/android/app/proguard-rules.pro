# TensorFlow Lite (LiteRT) is called through JNI and loads its optional GPU
# delegate by reflection: keep its classes and do not fail on the missing ones.
-keep class org.tensorflow.lite.** { *; }
-keep class com.google.ai.edge.litert.** { *; }
-dontwarn org.tensorflow.lite.**
-dontwarn com.google.ai.edge.litert.**
