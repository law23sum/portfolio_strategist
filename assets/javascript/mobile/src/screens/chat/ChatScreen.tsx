import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';
import { API_ENDPOINTS } from '../../config/api';

interface Message {
  id?: number;
  message_type: 'HUMAN' | 'AI';
  content: string | React.ReactNode;
  key?: number;
}

const ChatScreen = ({ route, navigation }: any) => {
  const [chatId, setChatId] = useState<number | null>(route?.params?.chatId || null);
  const [messages, setMessages] = useState<Message[]>([
    {
      key: -1,
      message_type: 'AI',
      content: 'Hello, what can I help you with today?',
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    if (chatId) {
      loadChat();
    } else {
      // Start a new chat if no chatId is provided
      startNewChat();
    }
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  useEffect(() => {
    if (currentTaskId && chatId) {
      const interval = setInterval(() => {
        checkTaskStatus();
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [currentTaskId, chatId]);

  const startNewChat = async () => {
    try {
      const response = await apiService.startChat();
      if (response.data && response.data.id) {
        const newChatId = response.data.id;
        setChatId(newChatId);
        // Update route params if navigation supports it
        if (navigation.setParams) {
          navigation.setParams({ chatId: newChatId });
        }
        // Update local state
        if (response.data.messages && response.data.messages.length > 0) {
          setMessages([
            {
              key: -1,
              message_type: 'AI',
              content: 'Hello, what can I help you with today?',
            },
            ...response.data.messages,
          ]);
        }
      }
    } catch (error) {
      console.error('Error starting chat:', error);
      // Show error message to user
      addMessage({
        message_type: 'AI',
        content: 'Unable to start a new chat. Please try again.',
      });
    }
  };

  const loadChat = async () => {
    if (!chatId) {
      startNewChat();
      return;
    }
    setLoading(true);
    try {
      const response = await apiService.getChat(chatId);
      if (response.data) {
        setMessages([
          {
            key: -1,
            message_type: 'AI',
            content: 'Hello, what can I help you with today?',
          },
          ...(response.data.messages || []),
        ]);
      }
    } catch (error) {
      console.error('Error loading chat:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkTaskStatus = async () => {
    if (!currentTaskId || !chatId) return;
    try {
      const response = await apiService.getChatResponse(chatId, currentTaskId);
      if (response.data) {
        if (response.data.complete) {
          if (response.data.success) {
            addMessage({
              message_type: 'AI',
              content: response.data.result.content || response.data.result,
            });
          } else {
            addMessage({
              message_type: 'AI',
              content: 'Sorry, something went wrong. Please try again.',
            });
          }
          setCurrentTaskId(null);
        }
      }
    } catch (error) {
      console.error('Error checking task status:', error);
      setCurrentTaskId(null);
    }
  };

  const addMessage = (message: Message) => {
    const newMessage = {
      ...message,
      key: Date.now(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    // If no chatId, start a new chat first
    if (!chatId) {
      await startNewChat();
      // Wait a bit for chat to be created, then retry
      setTimeout(() => {
        if (chatId) {
          sendMessage();
        }
      }, 500);
      return;
    }

    const userMessage: Message = {
      message_type: 'HUMAN',
      content: inputMessage,
      key: Date.now(),
    };
    addMessage(userMessage);
    const messageToSend = inputMessage;
    setInputMessage('');

    try {
      if (!chatId) {
        addMessage({
          message_type: 'AI',
          content: 'Please wait while we start a new chat...',
        });
        return;
      }
      const response = await apiService.sendChatMessage(chatId, messageToSend);
      if (response.data && response.data.task_id) {
        setCurrentTaskId(response.data.task_id);
      } else {
        addMessage({
          message_type: 'AI',
          content: 'Sorry, something went wrong. Please try again.',
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage({
        message_type: 'AI',
        content: 'Sorry, something went wrong. Please try again.',
      });
    }
  };

  const renderMessage = ({ item }: { item: Message }) => {
    const isHuman = item.message_type === 'HUMAN';
    return (
      <View
        style={[
          styles.messageContainer,
          isHuman ? styles.humanMessage : styles.aiMessage,
        ]}
      >
        <View style={styles.messageIcon}>
          {isHuman ? (
            <Icon name="person" size={24} color="#007AFF" />
          ) : (
            <Icon name="smart-toy" size={24} color="#4CAF50" />
          )}
        </View>
        <View style={styles.messageContent}>
          <Text style={styles.messageText}>
            {typeof item.content === 'string' ? item.content : 'Message'}
          </Text>
        </View>
      </View>
    );
  };

  const renderThinkingIndicator = () => {
    if (!currentTaskId) return null;
    return (
      <View style={[styles.messageContainer, styles.aiMessage]}>
        <View style={styles.messageIcon}>
          <Icon name="smart-toy" size={24} color="#4CAF50" />
        </View>
        <View style={styles.messageContent}>
          <View style={styles.thinkingContainer}>
            <ActivityIndicator size="small" color="#4CAF50" />
            <Text style={styles.thinkingText}>Thinking...</Text>
          </View>
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={styles.backButton}
        >
          <Icon name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Chat Assistant</Text>
        <View style={styles.backButton} />
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      ) : (
        <>
          <FlatList
            ref={flatListRef}
            data={messages}
            renderItem={renderMessage}
            keyExtractor={(item, index) => `message-${item.key || index}`}
            contentContainerStyle={styles.messagesList}
            ListFooterComponent={renderThinkingIndicator}
            onContentSizeChange={() => {
              flatListRef.current?.scrollToEnd({ animated: true });
            }}
          />

          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              value={inputMessage}
              onChangeText={setInputMessage}
              placeholder="Type your message..."
              placeholderTextColor="#999"
              multiline
              maxLength={1000}
            />
            <TouchableOpacity
              style={[
                styles.sendButton,
                !inputMessage.trim() && styles.sendButtonDisabled,
              ]}
              onPress={sendMessage}
              disabled={!inputMessage.trim() || !!currentTaskId}
            >
              <Icon name="send" size={24} color="#fff" />
            </TouchableOpacity>
          </View>
        </>
      )}
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 16,
    paddingTop: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  messagesList: {
    padding: 16,
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-start',
  },
  humanMessage: {
    justifyContent: 'flex-end',
  },
  aiMessage: {
    justifyContent: 'flex-start',
  },
  messageIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  messageContent: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 12,
    maxWidth: '80%',
  },
  messageText: {
    fontSize: 16,
    color: '#333',
    lineHeight: 22,
  },
  thinkingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  thinkingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    maxHeight: 100,
    marginRight: 8,
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
  },
});

export default ChatScreen;

