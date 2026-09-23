package com.nebula.search

import android.app.Application
import com.google.firebase.messaging.FirebaseMessaging

class NebulaApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // Initialize Firebase Messaging for push notifications
        FirebaseMessaging.getInstance().isAutoInitEnabled = true
    }
}