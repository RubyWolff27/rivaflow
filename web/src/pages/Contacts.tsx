import { useState, useEffect } from 'react';
import { contactsApi } from '../api/client';
import type { Contact } from '../types';
import { Users, Plus, Edit2, Trash2, Award, Filter } from 'lucide-react';

const BELT_COLORS: Record<string, string> = {
  white: 'bg-gray-100 text-gray-800 border-gray-300',
  blue: 'bg-blue-100 text-blue-800 border-blue-300',
  purple: 'bg-purple-100 text-purple-800 border-purple-300',
  brown: 'bg-amber-100 text-amber-800 border-amber-300',
  black: 'bg-gray-900 text-white border-gray-700',
};

export default function Contacts() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [filteredContacts, setFilteredContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    contact_type: 'training-partner' as 'instructor' | 'training-partner' | 'both',
    belt_rank: '' as '' | 'white' | 'blue' | 'purple' | 'brown' | 'black',
    belt_stripes: 0,
    instructor_certification: '',
    phone: '',
    email: '',
    notes: '',
  });

  useEffect(() => {
    loadContacts();
  }, []);

  useEffect(() => {
    filterContacts();
  }, [contacts, selectedFilter]);

  const loadContacts = async () => {
    setLoading(true);
    try {
      const response = await contactsApi.list();
      setContacts(response.data);
    } catch (error) {
      console.error('Error loading contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterContacts = () => {
    let filtered = [...contacts];

    if (selectedFilter === 'instructors') {
      filtered = filtered.filter(c => c.contact_type === 'instructor' || c.contact_type === 'both');
    } else if (selectedFilter === 'partners') {
      filtered = filtered.filter(c => c.contact_type === 'training-partner' || c.contact_type === 'both');
    }

    setFilteredContacts(filtered);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingContact) {
        await contactsApi.update(editingContact.id, {
          name: formData.name,
          contact_type: formData.contact_type,
          belt_rank: formData.belt_rank || undefined,
          belt_stripes: formData.belt_stripes,
          instructor_certification: formData.instructor_certification || undefined,
          phone: formData.phone || undefined,
          email: formData.email || undefined,
          notes: formData.notes || undefined,
        });
      } else {
        await contactsApi.create({
          name: formData.name,
          contact_type: formData.contact_type,
          belt_rank: formData.belt_rank || undefined,
          belt_stripes: formData.belt_stripes,
          instructor_certification: formData.instructor_certification || undefined,
          phone: formData.phone || undefined,
          email: formData.email || undefined,
          notes: formData.notes || undefined,
        });
      }

      resetForm();
      await loadContacts();
    } catch (error) {
      console.error('Error saving contact:', error);
      alert('Failed to save contact.');
    }
  };

  const handleEdit = (contact: Contact) => {
    setEditingContact(contact);
    setFormData({
      name: contact.name,
      contact_type: contact.contact_type,
      belt_rank: contact.belt_rank || '',
      belt_stripes: contact.belt_stripes || 0,
      instructor_certification: contact.instructor_certification || '',
      phone: contact.phone || '',
      email: contact.email || '',
      notes: contact.notes || '',
    });
    setShowAddForm(true);
  };

  const handleDelete = async (contactId: number) => {
    if (!confirm('Delete this contact? This cannot be undone.')) return;

    try {
      await contactsApi.delete(contactId);
      await loadContacts();
    } catch (error) {
      console.error('Error deleting contact:', error);
      alert('Failed to delete contact.');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      contact_type: 'training-partner',
      belt_rank: '',
      belt_stripes: 0,
      instructor_certification: '',
      phone: '',
      email: '',
      notes: '',
    });
    setEditingContact(null);
    setShowAddForm(false);
  };

  const renderBeltBadge = (contact: Contact) => {
    if (!contact.belt_rank) return null;

    const colorClass = BELT_COLORS[contact.belt_rank];
    const stripes = contact.belt_stripes || 0;

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${colorClass}`}>
        {contact.belt_rank.charAt(0).toUpperCase() + contact.belt_rank.slice(1)} Belt
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
            <h1 className="text-3xl font-bold">Contacts</h1>
            <p className="text-gray-600 dark:text-gray-400">
              {filteredContacts.length} of {contacts.length} contacts
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          {showAddForm ? 'Cancel' : 'Add Contact'}
        </button>
      </div>

      {/* Add/Edit Form */}
      {showAddForm && (
        <form onSubmit={handleSubmit} className="card bg-gray-50 dark:bg-gray-800 space-y-4">
          <h3 className="text-lg font-semibold">
            {editingContact ? 'Edit Contact' : 'Add New Contact'}
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
                value={formData.contact_type}
                onChange={(e) => setFormData({ ...formData, contact_type: e.target.value as any })}
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
              {editingContact ? 'Update Contact' : 'Add Contact'}
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
              All ({contacts.length})
            </button>
            <button
              onClick={() => setSelectedFilter('instructors')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFilter === 'instructors'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Instructors ({contacts.filter(c => c.contact_type === 'instructor' || c.contact_type === 'both').length})
            </button>
            <button
              onClick={() => setSelectedFilter('partners')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFilter === 'partners'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Training Partners ({contacts.filter(c => c.contact_type === 'training-partner' || c.contact_type === 'both').length})
            </button>
          </div>
        </div>
      </div>

      {/* Contacts List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredContacts.map(contact => (
          <div key={contact.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
                  {contact.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                  {contact.contact_type.replace('-', ' ')}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(contact)}
                  className="text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  title="Edit contact"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(contact.id)}
                  className="text-red-600 hover:text-red-700 dark:text-red-400"
                  title="Delete contact"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="space-y-2">
              {renderBeltBadge(contact)}

              {contact.instructor_certification && (
                <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                  <Award className="w-4 h-4" />
                  <span>{contact.instructor_certification}</span>
                </div>
              )}

              {contact.phone && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  📱 {contact.phone}
                </p>
              )}

              {contact.email && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  📧 {contact.email}
                </p>
              )}

              {contact.notes && (
                <p className="text-sm text-gray-500 dark:text-gray-500 italic">
                  {contact.notes}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredContacts.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          No contacts found. Add your first contact to get started!
        </div>
      )}
    </div>
  );
}
