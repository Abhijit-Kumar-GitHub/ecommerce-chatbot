import React, { useState, useEffect } from 'react';

const App = () => {
  const [user, setUser] = useState(null);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [products, setProducts] = useState([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
      setIsLoggedIn(true);
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (data.success) {
        setUser({ username: data.username });
        setIsLoggedIn(true);
        localStorage.setItem('user', JSON.stringify({ username: data.username }));
        setChatHistory([
          ...chatHistory,
          {
            sender: 'bot',
            message: `Welcome, ${data.username}! How can I help you shop today?`,
            timestamp: new Date().toLocaleString(),
          },
        ]);
      } else {
        alert(data.error || 'Invalid credentials');
      }
    } catch (error) {
      alert('Error during login');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;
    const newChat = { sender: 'user', message, timestamp: new Date().toLocaleString() };
    setChatHistory([...chatHistory, newChat]);
    setMessage('');
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: message }),
      });
      const data = await response.json();
      if (data.error) {
        setChatHistory((prev) => [
          ...prev,
          { sender: 'bot', message: data.error, timestamp: new Date().toLocaleString() },
        ]);
      } else {
        setProducts(data.products);
        const botMessage = data.products.length
          ? `Found ${data.products.length} products!`
          : 'No products found. Try another search.';
        setChatHistory((prev) => [
          ...prev,
          { sender: 'bot', message: botMessage, timestamp: new Date().toLocaleString() },
        ]);
      }
    } catch (error) {
      setChatHistory((prev) => [
        ...prev,
        { sender: 'bot', message: 'Error fetching products.', timestamp: new Date().toLocaleString() },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setChatHistory([]);
    setProducts([]);
    setMessage('');
    setChatHistory([
      {
        sender: 'bot',
        message: `Conversation reset. How can I assist you now, ${user?.username}?`,
        timestamp: new Date().toLocaleString(),
      },
    ]);
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    setUser(null);
    setIsLoggedIn(false);
    setChatHistory([]);
    setProducts([]);
  };

  if (!isLoggedIn) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-100">
        <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-2xl font-semibold text-gray-800">Login</h2>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mb-2 w-full rounded-md border p-2 border-gray-300"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-4 w-full rounded-md border p-2 border-gray-300"
            maxLength={10000}
          />
          <button
            onClick={handleLogin}
            disabled={isLoading}
            className="w-full rounded-md bg-primary p-2 text-white font-medium hover:bg-gray-800 disabled:bg-gray-600"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center justify-between p-4 bg-primary text-white">
        <h1 className="text-xl font-semibold">E-commerce Chatbot</h1>
        <button onClick={handleLogout} className="rounded-md bg-gray-700 p-2 hover:bg-gray-600">
          Logout
        </button>
      </header>
      <main className="flex-1 p-4 @container overflow-y-auto">
        <div className="mb-4 rounded-lg bg-white p-4 shadow-sm max-h-[calc(100vh-200px)] overflow-y-auto">
          {chatHistory.map((chat, index) => (
            <div
              key={index}
              className={`mb-2 ${chat.sender === 'user' ? 'text-right' : 'text-left'}`}
            >
              <div
                className={`inline-block p-2 rounded-lg ${
                  chat.sender === 'user' ? 'bg-blue-100' : 'bg-gray-100'
                }`}
              >
                <p className="text-sm">{chat.message}</p>
                <p className="text-xs text-gray-500">{chat.timestamp}</p>
              </div>
            </div>
          ))}
          {isLoading && <p className="text-center text-gray-600">Loading...</p>}
        </div>
        <div className="grid grid-cols-1 gap-4 @sm:grid-cols-2 @lg:grid-cols-3">
          {products.map((product) => (
            <div key={product.id} className="rounded-lg bg-white p-4 shadow-md hover:shadow-lg transition-shadow">
              <h3 className="text-lg font-medium text-gray-800">{product.name}</h3>
              <p className="text-sm text-gray-600">{product.description}</p>
              <p className="text-green-600 font-semibold">${product.price}</p>
              <button className="mt-2 w-full rounded-md bg-primary p-2 text-white font-medium hover:bg-gray-800">
                Add to Cart
              </button>
            </div>
          ))}
        </div>
      </main>
      <footer className="p-4 bg-gray-50">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type your query (e.g., 'show laptops under $1000')"
            className="flex-1 p-2 rounded-l-md border border-gray-600"
            maxLength={1000}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading}
            className="p-2 rounded-r-md bg-primary text-white hover:bg-gray-800 disabled:bg-gray-600"
          >
            Send
          </button>
          <button
            onClick={handleReset}
            className="p-2 rounded-md bg-gray-500 text-white hover:bg-gray-400"
          >
            Reset
          </button>
        </div>
      </footer>
    </div>
  );
};

export default App;