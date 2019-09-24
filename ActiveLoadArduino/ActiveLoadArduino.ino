#include <math.h>

//// VARIABLES & CONSTANTS
#define cutoffPin 5
#define currentPin 6
#define voltageSensePin 0
#define currentSensePin 1
#define RLoad 0.084
#define averageCount 10

String commandString = "";
String commandArgument = "";
const String startString = "Start\n";
const String stopString = "Stop\n";
bool commandComplete = false;
bool operating;

float setCutoffVoltage = 0.00;
int   mappedSetCutoffVoltage = 0; // Used to analogwrite

float setCurrent = 0.00;
int   mappedSetCurrent = 0;       // Used to analogwrite

float measuredVoltage = 0.00;     // Already mapped appropriately (different from calibration)
float measuredCurrent = 0.00;     // Already mapped appropriately
float voltageOffset = 0.00;
float currentOffset = 0.00;

float compensatedVoltage = 0.00;
float compensatedCurrent = 0.00;
float averagedVoltage = 0.00;
float averagedCurrent = 0.00;
int averageCounter;

//// INITIALISATION
void setup() {
  Serial.begin(115200);         // Start up Serial at 115200 Baud Rate
  commandString.reserve(48);    // Reserve 48 Bytes for the string
  commandArgument.reserve(24);  // Reserve 24 Bytes for the string
  operating = false;            // Set operating to false until PC is ready

  pinMode(cutoffPin, OUTPUT);
  pinMode(currentPin, OUTPUT);
  
  mappedSetCurrent = 10;       // Set a median value for the current to quickly converge to the proper value - Nah, start small
  measureValues();              // Make an intial measurement
  updateCompensatedValues();
  averageCounter = 0;
}


//// MAIN LOOP
void loop() {
   if (commandComplete) {
    processCommand(commandString);
    commandString = "";
    commandComplete = false;
  }

  // OUTPUT SIDE
  if(operating == true){
    adjustMappedValues();                                   // Adjust the output values (for the current) from previous Loop
    writeValues(mappedSetCutoffVoltage, mappedSetCurrent);  // Write the values to analog out
  }else if(operating == false){
    writeValues(0, 0);                                      // Set the outputs to 0V
  }else{
    writeValues(0, 0);                                      // Incase of error set to 0V
  }

  /// READ LIVE MEASURMENTS after setting current output and average
  measureValues();
  updateCompensatedValues();
  averagedVoltage += compensatedVoltage;
  averagedCurrent += compensatedCurrent;
  averageCounter++;

  if(averageCounter >= averageCount){ // Should count 10 times
    sendValues(); // Send Values over serial to PC
    averageCounter = 0;
    averagedVoltage = 0;
    averagedCurrent = 0;
  }
  delay(10); // With the average count to 10, should send data every 100ms
}



//// OTHER FUNCTIONS

void sendValues(){
  Serial.print(String(operating) + ",");
  Serial.print(String(averagedVoltage/averageCount) + ",");
  Serial.print(String(averagedCurrent/averageCount) + ",");
  Serial.println(String(setCutoffVoltage));
}

void adjustMappedValues(){
  if(compensatedCurrent < setCurrent){
    mappedSetCurrent++;
  }else if(compensatedCurrent > setCurrent){
    mappedSetCurrent--;
  }else if(compensatedCurrent == setCurrent){
    mappedSetCurrent += 0;
  }
}

void writeValues(int cutoffValue, int currentValue){
  analogWrite(cutoffPin, cutoffValue);
  analogWrite(currentPin, currentValue);
}

void measureValues(){
  measuredVoltage = fmap(analogRead(voltageSensePin), 0, 1023, 0.0, 5.0);
  measuredCurrent = fmap(analogRead(currentSensePin), 0, 1023, 0.0, 5.0)/RLoad;
}

void updateCompensatedValues(){
  compensatedVoltage = measuredVoltage + voltageOffset;
  compensatedCurrent = measuredCurrent + currentOffset;
}

// Process commands from master and reply with status
void processCommand(String command){
  if(command.equals(startString)){
    operating = true;
    Serial.println("Start OK");
    
  }else if(command.equals(stopString)){
    operating = false;
    Serial.println("Stop OK");

  }else if(command.startsWith("SetCutoffVoltage")){
    commandArgument = command.substring(17); // Get the string after the ='s
    setCutoffVoltage = commandArgument.toFloat();
    mappedSetCutoffVoltage = round(fmap(setCutoffVoltage, 0, 5.0, 0, 255)); // Used for output, no adjustment since no sense
    Serial.println("Cutoff is " + String(setCutoffVoltage));
    
  }else if(command.startsWith("SetCurrent")){
    commandArgument = command.substring(11);
    setCurrent = commandArgument.toFloat();
    Serial.println("Current is " + String(setCurrent));
    
  }else if(command.startsWith("VoltageOffset")){
    commandArgument = command.substring(14);
    voltageOffset = commandArgument.toFloat();
    Serial.println("VoltageOffset is " + String(voltageOffset));
    
  }else if(command.startsWith("CurrentOffset")){
    commandArgument = command.substring(14);
    currentOffset = commandArgument.toFloat();
    Serial.println("CurrentOffset is " + String(currentOffset));
    
  }else{
    Serial.println("Error, Recieved: " + command);
  }
}


/*
  SerialEvent occurs whenever a new data comes in the hardware serial RX. This
  routine is run between each time loop() runs, so using delay inside loop can
  delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    commandString += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      commandComplete = true;
    }
  }
}

// Map back to a float used for voltage calculation
float fmap(float x, float in_min, float in_max, float out_min, float out_max){
 return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}
