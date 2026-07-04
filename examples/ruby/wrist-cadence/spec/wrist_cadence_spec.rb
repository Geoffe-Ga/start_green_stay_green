# frozen_string_literal: true

require "spec_helper"
require_relative "../lib/wrist_cadence"

RSpec.describe WristCadence do
  describe ".hello" do
    it "runs without error" do
      # Test that the hello method exists and can be called.
      # This verifies the Hello World entry point works correctly.
      expect { described_class.hello }.not_to raise_error
    end

    it "prints hello message" do
      # Capture stdout to verify the hello message.
      pattern = /Hello from wrist-cadence/
      expect { described_class.hello }
        .to output(pattern).to_stdout
    end
  end
end
