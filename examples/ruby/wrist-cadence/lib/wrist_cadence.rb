# frozen_string_literal: true

# Entry point module for wrist-cadence.
module WristCadence
  VERSION = "0.1.0"

  def self.hello
    puts "Hello from wrist-cadence!"
  end
end

# Run hello if this file is executed directly
WristCadence.hello if __FILE__ == $PROGRAM_NAME
