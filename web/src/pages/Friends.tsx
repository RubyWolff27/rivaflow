import { useState, useEffect } from 'react';
import { friendsApi } from '../api/client';
import type { Friend } from '../types';
import { Users, Plus, Edit2, Trash2, Award, Filter } from 'lucide-react';

const BELT_COLORS: Record<string, string> = {
  white: 'bg-gray-100 text-gray-800 border-gray-300',
  blue: 'bg-blue-100 text-blue-800 border-blue-300',
  purple: 'bg-purple-100 text-purple-800 border-purple-300',
  brown: 'bg-amber-100 text-amber-800 border-amber-300',
  black: 'bg-gray-900 text-white border-gray-700',
};

export default function Friends() {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [filteredFriends, setFilteredFriends] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingFriend, setEditingFriend] = useState<Friend | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    friend_type: 'training-partner' as 'instructor' | 'training-partner' | 'both',
    belt_rank: '' as '' | 'white' | 'blue' | 'purple' | 'brown' | 'black',
    belt_stripes: 0,
    instructor_certification: '',
    phone: '',
    email: '',
    notes: '',
  });

  useEffect(() => {
    loadFriends();
  }, []);

  useEffect(() => {
    filterFriends();
  }, [friends, selectedFilter]);

  const loadFriends = async () => {
    setLoading(true);
    try {
      const response = await friendsApi.list();
      setFriends(response.data);
    } catch (error) {
      console.error('Error loading contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterFriends = () => {
    let filtered = [...friends];

    if (selectedFilter === 'instructors') {
      filtered = filtered.filter(c => c.friend_type === 'instructor' || c.friend_type === 'both');
    } else if (selectedFilter === 'partners') {
      filtered = filtered.filter(c => c.friend_type === 'training-partner' || c.friend_type === 'both');
    }

    setFilteredFriends(filtered);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingFriend) {
        await friendsApi.update(editingFriend.id, {
          name: formData.name,
          friend_type: formData.friend_type,
          belt_rank: formData.belt_rank || undefined,
          belt_stripes: formData.belt_stripes,
          instructor_certification: formData.instructor_certification || undefined,
          phone: formData.phone || undefined,
          email: formData.email || undefined,
          notes: formData.notes || undefined,
        });
      } else {
        await friendsApi.create({
          name: formData.name,
          friend_type: formData.friend_type,
          belt_rank: formData.belt_rank || undefined,
          belt_stripes: formData.belt_stripes,
          instructor_certification: formData.instructor_certification || undefined,
          phone: formData.phone || undefined,
          email: formData.email || undefined,
          notes: formData.notes || undefined,
        });
      }

      resetForm();
      await loadFriends();
    } catch (error) {
      console.error('Error saving contact:', error);
      alert('Failed to save contact.');
    }
  };

  const handleEdit = (friend: Friend) => {
    setEditingFriend(friend);
    setFormData({
      name: friend.name,
      friend_type: friend.friend_type,
      belt_rank: friend.belt_rank || '',
      belt_stripes: friend.belt_stripes || 0,
      instructor_certification: friend.instructor_certification || '',
      phone: friend.phone || '',
      email: friend.email || '',
      notes: friend.notes || '',
    });
    setShowAddForm(true);
  };

  const handleDelete = async (friendId: number) => {
    if (!confirm('Delete this friend? This cannot be undone.')) return;

    try {
      await friendsApi.delete(friendId);
      await loadFriends();
    } catch (error) {
      console.error('Error deleting friend:', error);
      alert('Failed to delete friend.');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      friend_type: 'training-partner',
      belt_rank: '',
      belt_stripes: 0,
      instructor_certification: '',
      phone: '',
      email: '',
      notes: '',
    });
    setEditingFriend(null);
    setShowAddForm(false);
  };

  const renderBeltBadge = (friend: Friend) => {
    if (!friend.belt_rank) return null;

    const colorClass = BELT_COLORS[friend.belt_rank];
    const stripes = friend.belt_stripes || 0;

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${colorClass}`}>
        {friend.belt_rank.charAt(0).toUpperCase() + friend.belt_rank.slice(1)} Belt
        {stripes > 0 && (
          <span className="flex gap-0.5 ml-1">
            {Array.from({ length: stripes }).map((_, i) => (
              <div key={i} className="w-1 h-3 bg-current opacity-70" />
            ))}
          </span>
        )}
      </span>
    );
  };

  if (loading) {
    return <div className="text-center py-12">Loading contacts...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="w-8 h-8 text-primary-600" />
          <div>
            <h1 className="text-3xl font-bold">Friends</h1>
            <p className="text-gray-600 dark:text-gray-400">
              {filteredFriends.length} of {friends.length} friends
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          {showAddForm ? 'Cancel' : 'Add Friend'}
        </button>
      </div>

      {/* Add/Edit Form */}
      {showAddForm && (
        <form onSubmit={handleSubmit} className="card bg-gray-50 dark:bg-gray-800 space-y-4">
          <h3 className="text-lg font-semibold">
            {editingFriend ? 'Edit Friend' : 'Add New Friend'}
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Name *</label>
              <input
                type="text"
                className="input"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Type</label>
              <select
                className="input"
                value={formData.friend_type}
                onChange={(e) => setFormData({ ...formData, friend_type: e.target.value as any })}
              >
                <option value="training-partner">Training Partner</option>
                <option value="instructor">Instructor</option>
                <option value="both">Both</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">Belt Rank</label>
              <select
                className="input"
                value={formData.belt_rank}
                onChange={(e) => setFormData({ ...formData, belt_rank: e.target.value as any })}
              >
                <option value="">None</option>
                <option value="white">White</option>
                <option value="blue">Blue</option>
                <option value="purple">Purple</option>
                <option value="brown">Brown</option>
                <option value="black">Black</option>
              </select>
            </div>
            <div>
              <label className="label">Stripes</label>
              <input
                type="number"
                className="input"
                value={formData.belt_stripes}
                onChange={(e) => setFormData({ ...formData, belt_stripes: parseInt(e.target.value) || 0 })}
                min="0"
                max="4"
              />
            </div>
            <div>
              <label className="label">Instructor Cert</label>
              <input
                type="text"
                className="input"
                value={formData.instructor_certification}
                onChange={(e) => setFormData({ ...formData, instructor_certification: e.target.value })}
                placeholder="e.g., 1st degree"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Phone</label>
              <input
                type="tel"
                className="input"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="label">Notes</label>
            <textarea
              className="input"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={2}
            />
          </div>

          <div className="flex gap-2">
            <button type="submit" className="btn-primary">
              {editingFriend ? 'Update Friend' : 'Add Friend'}
            </button>
            <button type="button" onClick={resetForm} className="btn-secondary">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-500" />
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedFilter('all')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFilter === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              All ({friends.length})
            </button>
            <button
              onClick={() => setSelectedFilter('instructors')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFilter === 'instructors'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Instructors ({friends.filter(c => c.friend_type === 'instructor' || c.friend_type === 'both').length})
            </button>
            <button
              onClick={() => setSelectedFilter('partners')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFilter === 'partners'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Training Partners ({friends.filter(c => c.friend_type === 'training-partner' || c.friend_type === 'both').length})
            </button>
          </div>
        </div>
      </div>

      {/* Contacts List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredFriends.map(friend => (
          <div key={friend.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
                  {friend.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                  {friend.friend_type.replace('-', ' ')}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(friend)}
                  className="text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  title="Edit friend"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(friend.id)}
                  className="text-red-600 hover:text-red-700 dark:text-red-400"
                  title="Delete friend"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="space-y-2">
              {renderBeltBadge(friend)}

              {friend.instructor_certification && (
                <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                  <Award className="w-4 h-4" />
                  <span>{friend.instructor_certification}</span>
                </div>
              )}

              {friend.phone && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  📱 {friend.phone}
                </p>
              )}

              {friend.email && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  📧 {friend.email}
                </p>
              )}

              {friend.notes && (
                <p className="text-sm text-gray-500 dark:text-gray-500 italic">
                  {friend.notes}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredFriends.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          No friends found. Add your first friend to get started!
        </div>
      )}
    </div>
  );
}
