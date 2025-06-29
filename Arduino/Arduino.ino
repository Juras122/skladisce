void setup() {
  Serial.begin(9600); // Ensure this matches your Python script's baud rate
}

void loop() {
  int S010000_val, S010001_val, S010002_val, S010003_val, S010004_val, S010005_val;

  // Read analog values
  S010000_val = analogRead(A0);
  S010001_val = analogRead(A1);
  S010002_val = analogRead(A2);
  S010003_val = analogRead(A3);
  S010004_val = analogRead(A4);
  S010005_val = analogRead(A5);

  // Print data in "ID:Value" format, separated by commas
  Serial.print("S010000:");
  Serial.print(S010000_val);
  Serial.print(",");
  Serial.print("S010001:");
  Serial.print(S010001_val);
  Serial.print(",");
  Serial.print("S010002:");
  Serial.print(S010002_val);
  Serial.print(",");
  Serial.print("S010003:");
  Serial.print(S010003_val);
  Serial.print(",");
  Serial.print("S010004:");
  Serial.print(S010004_val);
  Serial.print(",");
  Serial.print("S010005:");
  Serial.print(S010005_val);
  Serial.println(); // Newline after all data for easier parsing in Python

  delay(60000); // Wait for 60 seconds before the next reading
}