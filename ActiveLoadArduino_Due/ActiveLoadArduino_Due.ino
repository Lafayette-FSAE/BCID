#include <math.h>

//// VARIABLES & CONSTANTS
#define cutoffPin 2
#define currentPin 3
#define voltageSensePin A0
#define currentSensePin A1
#define RLoad 0.084
#define averageCount 250

String commandString = "";
String commandArgument = "";
const String startString = "Start\n";
const String stopString = "Stop\n";
bool commandComplete = false;
bool operating;

double setCutoffVoltage = 0.00;
int   mappedSetCutoffVoltage = 0; // Used to analogwrite

double setCurrent = 0.00;
int   mappedSetCurrent = 0;       // Used to analogwrite

double measuredVoltage = 0.00;     // Already mapped appropriately (different from calibration)
double measuredCurrent = 0.00;     // Already mapped appropriately
double voltageOffset = 0.00;
double currentOffset = 0.00;

double compensatedVoltage = 0.00;
double compensatedCurrent = 0.00;
double averagedVoltage = 0.00;
double averagedCurrent = 0.00;
int averageCounter;

double currentZeroPoint = 3095.0;
double ampPerBit = 81.0;





//// INITIALISATION
void setup() {
  SerialUSB.begin(115200);      // Start up SerialUSB at 115200 Baud Rate
  commandString.reserve(48);    // Reserve 48 Bytes for the string
  commandArgument.reserve(24);  // Reserve 24 Bytes for the string
  operating = false;            // Set operating to false until PC is ready

  pinMode(cutoffPin, OUTPUT);
  pinMode(currentPin, OUTPUT);
  analogReadResolution(12);
  analogWriteResolution(12);
  
  mappedSetCurrent = 1;       // Set a median value for the current to quickly converge to the proper value - Nah, start small
  measureValues();              // Make an intial measurement
  updateCompensatedValues();
  averageCounter = 0;
}



//// MAIN LOOP
void loop() {
   if (SerialUSB.available()) serialEvent();
  
   if (commandComplete) {
    processCommand(commandString);
    commandString = "";
    commandComplete = false;
  }

  if(operating == false){
    writeValues(0, 0);                                      // Set the outputs to 0V
    //SerialUSB.println("Turn off values");
  }

  /// READ LIVE MEASURMENTS after setting current output and average
  measureValues();                        // Measure
  updateCompensatedValues();              // Apply Offsets
  averagedVoltage += compensatedVoltage;  // Sum Voltages
  averagedCurrent += compensatedCurrent;  // Sum Currents
  averageCounter++;

  if(averageCounter >= averageCount){ // Should count x times
    averagedVoltage = averagedVoltage/averageCount;
    averagedCurrent = averagedCurrent/averageCount;

    sendValues(); // Send Values over SerialUSB to PC

    if(operating == true){
      adjustMappedValues();                                   // Adjust the output values (for the current) from previous Loop
      writeValues(mappedSetCutoffVoltage, mappedSetCurrent);  // Write the values to analog out
//      SerialUSB.print("Current Value: ");
//      SerialUSB.println(mappedSetCurrent);
    }
    
    averageCounter = 0;
    averagedVoltage = 0;
    averagedCurrent = 0;
  }
  delay(1); // With the average count to 10, should send data every 100ms
}





//// OTHER FUNCTIONS

void sendValues(){
  SerialUSB.print(String(operating) + ",");
  SerialUSB.print(String(averagedVoltage) + ",");
  SerialUSB.print(String(averagedCurrent) + ",");
  SerialUSB.println(String(setCutoffVoltage));
}

void adjustMappedValues(){
//  SerialUSB.print("Adjusting! Ave Current Value: ");
//  SerialUSB.print(averagedCurrent);
//  SerialUSB.print("  Percentage to target: ");
//  SerialUSB.println(abs(setCurrent - averagedCurrent)/setCurrent);

  if(abs(setCurrent - averagedCurrent) <= 0.10){ // Less than 100mA difference
    mappedSetCurrent += 0;
    return;
  }
  
  if(averagedCurrent < setCurrent && mappedSetCurrent < 4095){
    mappedSetCurrent++;
  }else if(averagedCurrent > setCurrent && mappedSetCurrent > 0){
    mappedSetCurrent--;
  }else if(averagedCurrent == setCurrent){
    mappedSetCurrent += 0;
  }
}

void writeValues(int cutoffValue, int currentValue){
  analogWrite(cutoffPin, cutoffValue);
  analogWrite(currentPin, currentValue);
}

void measureValues(){
  measuredVoltage = dmap(analogRead(voltageSensePin), 0, 4095, 0.0, 5.0);
  measuredCurrent = (currentZeroPoint - (double)analogRead(currentSensePin))/ampPerBit;
}

void updateCompensatedValues(){
  compensatedVoltage = measuredVoltage + voltageOffset;
  compensatedCurrent = measuredCurrent + currentOffset;
}

// Process commands from master and reply with status
void processCommand(String command){
  if(command.equals(startString)){
    operating = true;
    SerialUSB.println("Start OK");
    
  }else if(command.equals(stopString)){
    operating = false;
    SerialUSB.println("Stop OK");

  }else if(command.startsWith("SetCutoffVoltage")){
    commandArgument = command.substring(17); // Get the string after the ='s
    setCutoffVoltage = commandArgument.toDouble();
    mappedSetCutoffVoltage = round(dmap(setCutoffVoltage, 0, 3.3, 0, 4095)); // Used for output, no adjustment since no sense
    SerialUSB.println("Cutoff is " + String(setCutoffVoltage));
    
  }else if(command.startsWith("SetCurrent")){
    commandArgument = command.substring(11);
    setCurrent = commandArgument.toDouble();
    SerialUSB.println("Current is " + String(setCurrent));
    
  }else if(command.startsWith("VoltageOffset")){
    commandArgument = command.substring(14);
    voltageOffset = commandArgument.toDouble();
    SerialUSB.println("VoltageOffset is " + String(voltageOffset));
    
  }else if(command.startsWith("CurrentOffset")){
    commandArgument = command.substring(14);
    currentOffset = commandArgument.toDouble();
    SerialUSB.println("CurrentOffset is " + String(currentOffset));
    
  }else{
    SerialUSB.println("Error, Recieved: " + command);
  }
}


/*
  SerialEvent occurs whenever a new data comes in the hardware SerialUSB RX. This
  routine is run between each time loop() runs, so using delay inside loop can
  delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
  while (SerialUSB.available()) {
    // get the new byte:
    char inChar = (char)SerialUSB.read();
    // add it to the inputString:
    commandString += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      commandComplete = true;
    }
  }
}

// Map back to a double used for voltage calculation
double dmap(double x, double in_min, double in_max, double out_min, double out_max){
 return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
 }
