#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <DHT.h>

// Define your Wi-Fi credentials
const char *ssid = "YOUR WIFI SSID";
const char *password = "YOUR WIFI PASSWORD";

// Define the server URL where data will be sent
const char *serverUrl = "YOUR SERVER IP ADDRESS/add_data";

// Define the pin to which the DHT sensor is connected and the type of DHT sensor
#define DHTPIN 14
#define DHTTYPE DHT11

// Create a DHT object
DHT dht(DHTPIN, DHTTYPE);

void setup()
{
    // Initialize serial communication
    Serial.begin(115200);

    // Connect to Wi-Fi
    WiFi.begin(ssid, password);

    // Wait for Wi-Fi connection
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(1000);
        Serial.println("Connecting to Wi-Fi...");
    }

    Serial.println("Connected to Wi-Fi");

    // Initialize the DHT sensor
    dht.begin();
}

void loop()
{
    // Read humidity and temperature from the DHT sensor
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();

    // Check if the readings are valid
    if (!isnan(humidity) && !isnan(temperature))
    {
        // Send data to the server
        WiFiClient client;
        HTTPClient http;

        // Begin HTTP connection to the server
        if (http.begin(client, serverUrl))
        {
            // Set the content type header
            http.addHeader("Content-Type", "application/x-www-form-urlencoded");

            // Prepare the data to be sent
            String postData = "name=esp8266-1&humidity=" + String(humidity) + "&temperature=" + String(temperature);

            // Send a POST request with the data
            int httpResponseCode = http.POST(postData);

            // Check the HTTP response code
            if (httpResponseCode > 0)
            {
                Serial.print("HTTP Response code: ");
                Serial.println(httpResponseCode);
            }
            else
            {
                Serial.print("HTTP Error: ");
                Serial.println(httpResponseCode);
            }

            // End the HTTP connection
            http.end();
        }
    }

    // Delay for 1 minute before the next data transmission
    delay(60000);
}