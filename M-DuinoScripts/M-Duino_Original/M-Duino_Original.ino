const int ArmLight = R0_5;

const int HotWire1 = R0_6;

const int HotWire2 = R0_7;

const int HotWire3 = R0_8;

 

const int Trigger = I0_4;

const int Mode = I0_5;

const int Arm = I0_3;

 

const int SparkOut = Q0_1;

const int DAQTrig = Q0_0;

 

int active;

int times = 0;

int dwell = 5000;

int BurnTime = 10;

int Delay = 500;

int count;

boolean flag = false;

boolean Armed = false;

boolean Fail = false;

boolean Fired = false;

boolean HotWire = false;

 

void setup() {

pinMode(Trigger, INPUT);

pinMode(Mode, INPUT);

pinMode(Arm, INPUT);

pinMode(HotWire, OUTPUT);

pinMode(SparkOut, OUTPUT);

pinMode(DAQTrig, OUTPUT);

pinMode(ArmLight, OUTPUT);

Serial.begin(9600);

}

void Melty() {

            digitalWrite(HotWire1, HIGH);

            digitalWrite(HotWire2, HIGH);

            digitalWrite(HotWire3, HIGH);

            for(count = 0; count < BurnTime ; count++)

            {

            delay(1000);

            }

            digitalWrite(HotWire1, LOW);

            digitalWrite(HotWire2, LOW);

            digitalWrite(HotWire3, LOW);

 

}

void ConstSpark(){

 

  if (digitalRead(Arm) == 1)    

  {

    digitalWrite(ArmLight, HIGH);

    digitalWrite(SparkOut, HIGH);

    delayMicroseconds(dwell);

    digitalWrite(SparkOut, LOW);

   

  }

  else

  {

    digitalWrite(ArmLight, LOW);

    digitalWrite(SparkOut, LOW);

  }

}

void HydrogenTest(){

if ((digitalRead(Trigger) == 0) && (digitalRead(Arm) == 0))

  {Fired = false;

    Fail = false;

    }

if ((digitalRead(Trigger) == 1) && (digitalRead(Arm) == 0))

   {Fail = true;}

 

if ((Fail == false) && (digitalRead(Arm) == 1)  && (Fired == false) /*&& (digitalRead(Trigger) != 1)*/)

    { Armed = true;

      digitalWrite(ArmLight,HIGH);

    }

  else { Armed = false;

         digitalWrite(ArmLight,LOW);

         }  

 

if ((digitalRead(Trigger) == 1) && (Armed == true) && (Fired == false))

    {

      if ((flag == false) && (Fired == false))

         {for(times = 0; times < 1; times++)

            {if (HotWire == true)

            {Melty();}

            digitalWrite(SparkOut, HIGH);

            delayMicroseconds(dwell-Delay);

            digitalWrite(DAQTrig, HIGH);

            delayMicroseconds(Delay);

            digitalWrite(SparkOut, LOW);

            digitalWrite(DAQTrig, LOW);

            Fired = true;

            delay(100);

            }

          flag = true;

        }

        }

     

      else

      {

 

      digitalWrite(DAQTrig, LOW);

 

      flag = false;

      Armed = false;

     

      }

  if ( Fired == true)

    {Armed = false;

    digitalWrite(ArmLight,LOW);

    digitalWrite(HotWire, LOW);

    digitalWrite(DAQTrig, LOW);

    }

}

/*

const int Trigger = I0_3;

const int Mode = I0_4;

const int Arm = I0_5;

*/

void loop() {

 

if (digitalRead(Mode) == 1){

  ConstSpark();

  }

  else{

    HydrogenTest();

  }

 

Serial.print(digitalRead(Mode));

Serial.print(digitalRead(Arm));

Serial.print(digitalRead(Trigger));

Serial.print('\t');

Serial.print(Fired);

Serial.print(Fail);

Serial.print(Armed);

Serial.println(flag);

 

}