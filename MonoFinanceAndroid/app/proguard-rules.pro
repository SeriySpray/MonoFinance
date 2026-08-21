# Proguard rules for MonoFinance app
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod

# Keep Gson model structures
-keep class com.google.gson.** { *; }
-keep class com.monofinance.app.** { *; }
