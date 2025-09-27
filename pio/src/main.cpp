#include <Arduino.h>

#include <ic/SST39SF0x0.h>
#include <ic/AT28C64.h>
#include <ic/AT28C256.h>

#define CMD_BYTE 0x7E

enum class Command { IDLE,
  READ,
  WRITE,
  PAGE_WRITE,
  ERASE_SECTOR,
  ERASE_CHIP
} command = Command::IDLE;

enum class ICType {
  BASE,
  SST39SF010,
  SST39SF020,
  SST39SF040,
  AT28C64,
  AT28C256
} icType;

SST39SF010 sst39sf010;
SST39SF020 sst39sf020;
SST39SF040 sst39sf040;
AT28C64 at28c64;
AT28C256 at28c256;

int consumeNext(uint8_t* ptr);
void setICType(ICType ic);
void setCommand(Command c);

int parseAddress(uint32_t* address);
int parseData(uint8_t* data);

void readMode();
void writeMode();
int8_t setAddress(uint32_t address);
uint8_t read(uint32_t address);
int8_t write(uint32_t address, uint8_t data);
int8_t writePage(uint32_t pageIndex, uint8_t data);
int8_t eraseSector(uint8_t sector);
int8_t eraseChip();

uint8_t buffer[256];

void setup() {
  Serial.begin(500000);
}

void loop() {
  uint32_t address = 0;
  uint32_t end = 0;
  uint8_t data = 0;

  switch (command) {
    case Command::IDLE:
      while (!consumeNext(nullptr)); // Wait for a command
      break;
    case Command::READ:
      if (parseAddress(&address)) break;
      if (parseAddress(&end)) break;

      ICTester::tester.busy();

      for (; address < end; ++address) {
        Serial.write(read(address));
      }

      ICTester::tester.ready();

      break;
    case Command::WRITE:
      if (parseAddress(&address)) break;

      ICTester::tester.busy();

      while (!parseData(&data)) {
        Serial.write(write(address, data));
        ++address;
      }

      ICTester::tester.ready();

      break;
    case Command::PAGE_WRITE:
      if (parseAddress(&address)) break;

      ICTester::tester.busy();
      {
        setAddress(address);

        uint16_t pageIndex = address & 0xff;
        for (; pageIndex < 256; ++pageIndex) {
          if (parseData(buffer + pageIndex)) return;
        }

        for (pageIndex = address & 0xff; pageIndex < 256; ++pageIndex) {
          writePage(pageIndex & 0x3f, buffer[pageIndex]);

          if ((pageIndex & 0x3f) == 0x3f) {
            delay(6);
            address += 64;
            setAddress(address);
          }
        }

        Serial.write(0);
      }
      ICTester::tester.ready();
       
      break;
    case Command::ERASE_SECTOR:
      if (parseData(&data)) break;

      ICTester::tester.busy();
      Serial.write(eraseSector(data));
      ICTester::tester.ready();
      break;
    case Command::ERASE_CHIP:
      ICTester::tester.busy();
      Serial.write(eraseChip());
      ICTester::tester.ready();
      consumeNext(nullptr);
      break;
  }
}

int consumeNext(uint8_t* ptr) {
  uint8_t cmdBytes = 0;
  uint8_t c;

  while (1) {
    while(!Serial.available());

    if ((c = Serial.read()) != CMD_BYTE && cmdBytes) { // Previous c was a CMD_BYTE and current c is not -> we got a command.
      if (c & 0x80) { // If bit 7 is set, the command sets the used ic.
        setICType((ICType) (c & 0x7f));
      } else { // Otherwise, the command sets the current operation.
        setCommand((Command) (c & 0x7f));
      }
      return 1;
    } else if (c == CMD_BYTE && !cmdBytes) { // Found a CMD_BYTE, might be the start of a command.
      ++cmdBytes;
    } else { // Regular data.
      if (ptr != nullptr) *ptr = c;
      return 0;
    }
  }
}

void setICType(ICType ic) {
  switch (icType) {
    case ICType::SST39SF010:
      sst39sf010.disable();
      break;
    case ICType::SST39SF020:
      sst39sf020.disable();
      break;
    case ICType::SST39SF040:
      sst39sf040.disable();
      break;
    case ICType::AT28C64:
      at28c64.disable();
      break;
    case ICType::AT28C256:
      at28c256.disable();
      break;
    default:
      break;
  }

  icType = ic;

  switch (icType) {
    case ICType::SST39SF010:
      sst39sf010.enable();
      break;
    case ICType::SST39SF020:
      sst39sf020.enable();
      break;
    case ICType::SST39SF040:
      sst39sf040.enable();
      break;
    case ICType::AT28C64:
      at28c64.enable();
      break;
    case ICType::AT28C256:
      at28c256.enable();
      break;
    default:
      break;
  }
}

void setCommand(Command c) {
  command = c;

  switch (command) {
    case Command::IDLE:
    case Command::READ:
      readMode();
      break;
    case Command::WRITE:
    case Command::PAGE_WRITE:
    case Command::ERASE_SECTOR:
    case Command::ERASE_CHIP:
      writeMode();
      break;
  }
}
int parseAddress(uint32_t* address) {
  if (consumeNext((uint8_t*) address + 0)) return 1; // Byte 0
  if (consumeNext((uint8_t*) address + 1)) return 1; // Byte 1
  if (consumeNext((uint8_t*) address + 2)) return 1; // Byte 2
  if (consumeNext((uint8_t*) address + 3)) return 1; // Byte 3
  return 0;
}

int parseData(uint8_t* data) {
  if (consumeNext(data)) return 1;
  else return 0;
}

void readMode() {
  switch (icType) {
    case ICType::SST39SF010:
      sst39sf010.readMode();
      break;
    case ICType::SST39SF020:
      sst39sf020.readMode();
      break;
    case ICType::SST39SF040:
      sst39sf040.readMode();
      break;
    case ICType::AT28C64:
      at28c64.readMode();
      break;
    case ICType::AT28C256:
      at28c256.readMode();
      break;
    default:
      break;
  }
}

void writeMode() {
  switch (icType) {
    case ICType::SST39SF010:
      sst39sf010.writeMode();
      break;
    case ICType::SST39SF020:
      sst39sf020.writeMode();
      break;
    case ICType::SST39SF040:
      sst39sf040.writeMode();
      break;
    case ICType::AT28C64:
      at28c64.writeMode();
      break;
    case ICType::AT28C256:
      at28c256.writeMode();
      break;
    default:
      break;
  }
}

int8_t setAddress(uint32_t address) {
  switch (icType) {
    case ICType::SST39SF010:
      sst39sf010.setAddress(address);
      return 0;
    case ICType::SST39SF020:
      sst39sf020.setAddress(address);
      return 0;
    case ICType::SST39SF040:
      sst39sf040.setAddress(address);
      return 0;
    case ICType::AT28C64:
      at28c64.setAddress(address);
      return 0;
    case ICType::AT28C256:
      at28c256.setAddress(address);
      return 0;
    default:
      return 1;
  }
}

uint8_t read(uint32_t address) {
  switch (icType) {
    case ICType::SST39SF010:
      return sst39sf010.read(address);
    case ICType::SST39SF020:
      return sst39sf020.read(address);
    case ICType::SST39SF040:
      return sst39sf040.read(address);
    case ICType::AT28C64:
      return at28c64.read(address);
    case ICType::AT28C256:
      return at28c256.read(address);
    default:
      return 0;
  }
}

int8_t write(uint32_t address, uint8_t data) {
  switch (icType) {
    case ICType::SST39SF010:
      sst39sf010.write(address, data);
      return 0;
    case ICType::SST39SF020:
      sst39sf020.write(address, data);
      return 0;
    case ICType::SST39SF040:
      sst39sf040.write(address, data);
      return 0;
    case ICType::AT28C64:
      at28c64.write(address, data);
      return 0;
    case ICType::AT28C256:
      at28c256.write(address, data);
      return 0;
    default:
      return 1;
  }
}

int8_t writePage(uint32_t pageIndex, uint8_t data) {
  switch (icType) {
    case ICType::AT28C256:
      at28c256.writePage(pageIndex, data);
      return 0;
    default:
      return 1;
  }
}

int8_t eraseSector(uint8_t sector) {
  switch (icType) {
    case ICType::SST39SF010:
      sst39sf010.eraseSector(sector);
      return 0;
    case ICType::SST39SF020:
      sst39sf020.eraseSector(sector);
      return 0;
    case ICType::SST39SF040:
      sst39sf040.eraseSector(sector);
      return 0;
    default:
      return 1;
  }
}

int8_t eraseChip() {
  switch (icType) {
    case ICType::SST39SF010:
      sst39sf010.eraseChip();
      return 0;
    case ICType::SST39SF020:
      sst39sf020.eraseChip();
      return 0;
    case ICType::SST39SF040:
      sst39sf040.eraseChip();
      return 0;
    case ICType::AT28C256:
      at28c256.eraseChip();
      return 0;
    default:
      return 1;
  }
}
