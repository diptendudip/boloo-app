/**
 * ConfirmationModal Component
 *
 * Web-compatible replacement for React Native Alert.alert()
 * Works on iOS, Android, AND Web (Expo Web)
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  StyleSheet,
  ScrollView,
  Platform,
} from 'react-native';

interface ConfirmationButton {
  text: string;
  onPress?: () => void;
  style?: 'default' | 'cancel' | 'destructive';
}

interface ConfirmationModalProps {
  visible: boolean;
  title: string;
  message: string;
  buttons: ConfirmationButton[];
  onClose: () => void;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  visible,
  title,
  message,
  buttons,
  onClose,
}) => {
  const handleButtonPress = (button: ConfirmationButton) => {
    onClose();
    if (button.onPress) {
      button.onPress();
    }
  };

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          {/* Title */}
          <Text style={styles.title}>{title}</Text>

          {/* Message (scrollable for long content) */}
          <ScrollView
            style={styles.messageContainer}
            showsVerticalScrollIndicator={true}
          >
            <Text style={styles.message}>{message}</Text>
          </ScrollView>

          {/* Buttons */}
          <View style={styles.buttonContainer}>
            {buttons.map((button, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.button,
                  button.style === 'cancel' && styles.cancelButton,
                  button.style === 'destructive' && styles.destructiveButton,
                  index > 0 && styles.buttonMarginLeft,
                ]}
                onPress={() => handleButtonPress(button)}
              >
                <Text
                  style={[
                    styles.buttonText,
                    button.style === 'cancel' && styles.cancelButtonText,
                    button.style === 'destructive' && styles.destructiveButtonText,
                  ]}
                >
                  {button.text}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </View>
    </Modal>
  );
};

/**
 * Cross-platform alert function that works on web
 * Use this instead of Alert.alert for web compatibility
 */
export const showAlert = (
  title: string,
  message: string,
  buttons?: ConfirmationButton[]
): Promise<number> => {
  return new Promise((resolve) => {
    if (Platform.OS === 'web') {
      // Use window.confirm for simple yes/no dialogs on web
      if (buttons && buttons.length === 2) {
        const confirmed = window.confirm(`${title}\n\n${message}`);
        const confirmIndex = buttons.findIndex(b => b.style !== 'cancel');
        const cancelIndex = buttons.findIndex(b => b.style === 'cancel');

        if (confirmed) {
          buttons[confirmIndex]?.onPress?.();
          resolve(confirmIndex);
        } else {
          buttons[cancelIndex]?.onPress?.();
          resolve(cancelIndex);
        }
      } else if (buttons && buttons.length === 1) {
        window.alert(`${title}\n\n${message}`);
        buttons[0]?.onPress?.();
        resolve(0);
      } else {
        window.alert(`${title}\n\n${message}`);
        resolve(0);
      }
    } else {
      // Use native Alert on iOS/Android
      const { Alert } = require('react-native');
      Alert.alert(title, message, buttons);
      resolve(0);
    }
  });
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContainer: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 400,
    maxHeight: '80%',
    ...Platform.select({
      web: {
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
      },
      default: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.15,
        shadowRadius: 20,
        elevation: 8,
      },
    }),
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  messageContainer: {
    maxHeight: 300,
    marginBottom: 20,
  },
  message: {
    fontSize: 16,
    lineHeight: 24,
    color: '#555',
    textAlign: 'left',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  button: {
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    minWidth: 100,
    alignItems: 'center',
  },
  buttonMarginLeft: {
    marginLeft: 12,
  },
  cancelButton: {
    backgroundColor: '#f5f5f5',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  destructiveButton: {
    backgroundColor: '#FF3B30',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  cancelButtonText: {
    color: '#666',
  },
  destructiveButtonText: {
    color: '#fff',
  },
});

export default ConfirmationModal;
